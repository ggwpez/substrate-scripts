use subxt::{
    PolkadotConfig,
    OnlineClient,
};
use hex_literal::hex;
use subxt::blocks::BlockRef;
use subxt::config::substrate::H256;
use westmint::runtime_types::asset_hub_westend_runtime::RuntimeEvent;
use westmint::runtime_types::pallet_balances::pallet::Event as BalancesEvent;
use westmint::runtime_types::pallet_ah_migrator::pallet::Event as AhMigratorEvent;
use serde::{Serialize, Deserialize};
use std::fs::File;
use std::io::BufWriter;
use subxt::config::substrate::AccountId32;

#[subxt::subxt(
    runtime_metadata_path = "westmint_metadata.scale",
    substitute_type(path = "sp_staking::ExposurePage<A,B>", with = "crate::custom_types::ExposurePage<A,B>"),
    substitute_type(path = "sp_staking::IndividualExposure<A>", with = "crate::custom_types::IndividualExposure<A>"),
    substitute_type(path = "sp_staking::PagedExposureMetadata<A>", with = "crate::custom_types::PagedExposureMetadata<A>"),
)]
pub mod westmint {}

type WestmintConfig = PolkadotConfig; // same for our use-case

// https://assethub-westend.subscan.io/event?block=11736080
const SECOND_MIGRATION_START: u32 = 11736080;
// https://assethub-westend.subscan.io/event?block=11736597
const SECOND_MIGRATION_FINISH: [u8; 32] = hex!("904e2af8b15fffb67df42a4bc86037a8e7304d3e3e53aaa1cd9ff262acd02588");

/// Serializable version of `RuntimeEvent`
#[derive(Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum BadEvent {
    Unreserved {
        amount: u128, // Balance first so we sort by it
        who: AccountId32,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    let api = OnlineClient::<WestmintConfig>::from_url("wss://westend-asset-hub-rpc.polkadot.io:443").await?;
    println!("Connection with parachain established.");

    let hash: H256 = SECOND_MIGRATION_FINISH.into();
    let mut block = api.blocks().at(BlockRef::from(hash)).await?;

    // The events that we want to roll back since they were wrong
    let mut bad_events = Vec::new();

    // Iterate backwards until we hit our first block
    while block.number() >= SECOND_MIGRATION_START {       
        let events = api.events().at(block.hash()).await?;

        let mut events = events.iter();
        // We only care about the events between `BatchReceived` and `BatchProcessed`.

        let mut batch_received = false;

        while let Some(event) = events.next() {
            let event = event.expect("Must parse events");
            
            // First, find the `BatchReceived` event.
            match event.as_root_event::<westmint::Event>().expect("Must parse event") {
                RuntimeEvent::AhMigrator(AhMigratorEvent::BatchReceived { .. }) => {
                    log::info!("Batch received");
                    batch_received = true;                    
                    break;
                },
                _ => (),
            }
        }

        // Now keep all events until we hit the `BatchProcessed` event.
        if batch_received {
            while let Some(event) = events.next() {
                let event = event.expect("Must parse events");

                match event.as_root_event::<westmint::Event>().expect("Must parse event") {
                    RuntimeEvent::AhMigrator(AhMigratorEvent::BatchProcessed { .. }) => {
                        log::info!("Batch processed");
                        break;
                    },
                    RuntimeEvent::Balances(BalancesEvent::Unreserved { who, amount }) if amount > 0 => {
                        log::info!("Unreserved {:?} amount {:?}", who, amount);
                        bad_events.push(BadEvent::Unreserved { who, amount });
                    },
                    _ => (),
                }
            }
        } else {
            log::debug!("No batch received in block {}", block.number());
        }
        
        // goto parent block
        log::debug!("Fetching block: {}", block.number() - 1);
        block = api.blocks().at(block.header().parent_hash).await?;
    }

    // Write the bad events to a JSON file
    bad_events.sort();
    let file = File::create("bad-events.json").expect("Must create file");
    let writer = BufWriter::new(file);
    serde_json::to_writer_pretty(writer, &bad_events).expect("Must write events to file");

    Ok(())
}

mod custom_types {
    use codec::{Decode, Encode};
    use scale_encode::EncodeAsType;
    use scale_decode::DecodeAsType;

    #[derive(Decode, Encode, DecodeAsType, EncodeAsType, Debug)]
    pub struct ExposurePage<_0, _1> {
        pub page_total: _1,
        pub others: Vec<IndividualExposure<_0, _1>>,
    }

    #[derive(Decode, Encode, DecodeAsType, EncodeAsType, Debug)]
    pub struct IndividualExposure<_0, _1> {
        pub who: _0,
        pub value: _1,
    }

    #[derive(Decode, Encode, DecodeAsType, EncodeAsType, Debug)]
    pub struct PagedExposureMetadata<_0> {
        pub total: _0,
        pub own: _0,
        pub nominator_count: ::core::primitive::u32,
        pub page_count: ::core::primitive::u32,
    }
}
