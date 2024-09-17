// `dot` is the name we gave to `npx papi add`
import { collectives, polkadot, kusama } from "@polkadot-api/descriptors";
import { createClient } from "polkadot-api";
import { chainSpec as polkadotChainSpec } from "polkadot-api/chains/polkadot";
import { chainSpec as kusamaChainSpec } from "polkadot-api/chains/ksmcc3";
import { chainSpec as collectivesChainSpec } from "polkadot-api/chains/polkadot_collectives";
import { getSmProvider } from "polkadot-api/sm-provider";
import { smoldot } from "./smoldot.js"
import { fromHex, toHex } from "@polkadot-api/utils"
import { AccountId } from "@polkadot-api/substrate-bindings"
import { getPolkadotSigner } from "polkadot-api/signer"
import { ed25519 } from "@noble/curves/ed25519"
import 'dotenv/config'
import util from "node:util";
import { exec } from 'child_process';

// Account setup
const SK = process.env.SECRET || "0xabf8e5bdbe30c65656c0a3cbd181ff8a56294a69dfedd27982aace4a76909115" // Alice;
const aliceEd25519PrivKey = fromHex(SK)

const signer = getPolkadotSigner(
  ed25519.getPublicKey(aliceEd25519PrivKey),
  "ed25519",
  (input) => ed25519.sign(input, aliceEd25519PrivKey),
)

let acc = AccountId().dec(signer.publicKey);
console.log(`Using account ${acc}`);

// API setup
const smoldotRelayChain = await smoldot.addChain({
  chainSpec: polkadotChainSpec,
});

const collectiveRelayChain = await smoldot.addChain({
  chainSpec: collectivesChainSpec,
  potentialRelayChains: [smoldotRelayChain],
});

const smoldotKusamaChain = await smoldot.addChain({
  chainSpec: kusamaChainSpec,
});

async function check(api, pallet_name, name) {
  // Filter referenda
  const referenda = await api.query[pallet_name].ReferendumInfoFor.getEntries();
  var to_be_refunded = [];

  for (const { keyArgs, value } of referenda) {
    if (value.type != "Approved" && value.type != "Rejected")
      continue;

    if (value.value[2] == undefined)
      continue;
    const decision_deposit = value.value[2].amount;

    console.log(`Referendum ${keyArgs[0]} can be refunded with ${decision_deposit}`);
    to_be_refunded.push({ referendum_id: keyArgs[0] });
  }

  // Early exit
  if (to_be_refunded.length == 0) {
    console.log(`[${name}/${pallet_name}] No referenda to refund`);
    return;
  }

  // Send refund transactions
  console.log(`Refunding ${to_be_refunded.length} referenda`);

  for (const { referendum_id } of to_be_refunded) {
    console.log(`Refunding referendum ${referendum_id}`);

    const refund = api.tx[pallet_name].refund_decision_deposit({ index: referendum_id });
    const finalCall = refund;//await findVanity(api, batchCall);

    await finalCall.signAndSubmit(signer)
      .then(() => {
        console.log(`Refunded referendum ${referendum_id}`);
        exec(`osascript -e 'display notification "Refunded ref ${referendum_id} on ${name}" with title "Refunded referendum"'`)
      })
      .catch((err) => {
        console.error(`Failed to refund referendum ${referendum_id}: ${err}`);
      })
  }
}

// Polkadot
{
  const relayJsonRpcProvider = getSmProvider(smoldotRelayChain);
  const relayClient = createClient(relayJsonRpcProvider);
  const relayApi = relayClient.getTypedApi(polkadot);

  await check(relayApi, "Referenda", "Polkadot");
}

// Collectives
{
  const collectiveJsonRpcProvider = getSmProvider(collectiveRelayChain);
  const collectivesClient = createClient(collectiveJsonRpcProvider);
  const api = collectivesClient.getTypedApi(collectives);

  await check(api, "FellowshipReferenda", "Collectives");
  await check(api, "AmbassadorReferenda", "Collectives");
}

// Kusama
{
  const relayJsonRpcProvider = getSmProvider(smoldotKusamaChain);
  const relayClient = createClient(relayJsonRpcProvider);
  const relayApi = relayClient.getTypedApi(kusama);

  await check(relayApi, "Referenda", "Kusama");
  await check(relayApi, "FellowshipReferenda", "Kusama");
}

process.exit(0);
