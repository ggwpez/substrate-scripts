use subxt::{
    OnlineClient,
    PolkadotConfig
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let api = OnlineClient::<PolkadotConfig>::from_url("ws://127.0.0.1:9944").await?;
    

    // The length of each KV pair.
    let mut kv_lens = Vec::<(u64, u64)>::new();
    let mut last_key = Vec::<u8>::new();

    let hash = api.rpc().finalized_head().await?;
    loop {
        let keys = api.rpc().storage_keys_paged(&[], 1000, &last_key, Some(hash)).await?;
        println!("Queried {} more keys, {} in total", keys.len(), total);
        total += keys.len();
        let Some(last) = keys.iter().last() else {
            break;
        };
        last_key = last.as_ref().into();

        let values = api.rpc().query_storage_at(keys, Some(hash));
        for key in keys.iter() {
        }
    }

    Ok(())
}
