import { polkadot, ConvictionVotingVoteAccountVote, MultiAddress } from "@polkadot-api/descriptors";
import { createClient, Binary } from "polkadot-api";
import { chainSpec as polkadotChainSpec } from "polkadot-api/chains/polkadot";
import { getSmProvider } from "polkadot-api/sm-provider";
import { smoldot } from "./smoldot.js";
import { toHex, fromHex } from "@polkadot-api/utils";
import { AccountId } from "@polkadot-api/substrate-bindings";
import { getPolkadotSigner } from "polkadot-api/signer";
import { ed25519 } from "@noble/curves/ed25519";
import dotenv from 'dotenv';
import { Command } from 'commander';
import util from "node:util";
import { exec } from 'child_process';

import {
  createKeyMulti,
  encodeAddress,
  sortAddresses
} from '@polkadot/util-crypto';

dotenv.config({ path: '.env' });

// Account setup
const SK = process.env.SENDER_URI;
const aliceEd25519PrivKey = fromHex(SK);

const signer = getPolkadotSigner(
  ed25519.getPublicKey(aliceEd25519PrivKey),
  "ed25519",
  (input) => ed25519.sign(input, aliceEd25519PrivKey),
);

let acc = AccountId().dec(signer.publicKey);
console.log(`Using account ${acc}`);

// Parse command line arguments
const program = new Command();
program
  .option('--ayes <numbers...>', 'Proposal IDs to vote AYE for', [])
  .option('--nays <numbers...>', 'Proposal IDs to vote NAY for', [])
  .parse(process.argv);

const options = program.opts();

if (options.ayes.length === 0 && options.nays.length === 0) {
  console.error("Error: You must provide at least one proposal ID to vote for.");
  process.exit(1);
}

// Prepare votes
const votes = {};
options.ayes.forEach(id => votes[parseInt(id)] = true);
options.nays.forEach(id => votes[parseInt(id)] = false);

// API setup
async function main() {
  const smoldotRelayChain = await smoldot.addChain({
    chainSpec: polkadotChainSpec,
  });

  const relayJsonRpcProvider = getSmProvider(smoldotRelayChain);
  const relayClient = createClient(relayJsonRpcProvider);
  const api = relayClient.getTypedApi(polkadot);

  console.log(`Connected to ${(await relayClient.getChainSpecData()).name}`);

  // Create batch calls
  var txs = []
  for (const [pollIndex, vote] of Object.entries(votes)) {
	const conviction = (vote ? 128 : 0) + 6;
    const tx = api.tx.ConvictionVoting.vote({
      poll_index: parseInt(pollIndex),
      vote: ConvictionVotingVoteAccountVote.Standard({
      vote: conviction,
      balance: 150000000000000n,
      })
    });
	  txs.push(tx.decodedCall);
  }
  // also put a remark for good measures
  const tx = api.tx.System.remark({ remark: Binary.fromHex('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF') });
  txs.push(tx.decodedCall);

  // Create batch call
  const batchCall = api.tx.Utility.force_batch({calls: txs});

  // Create proxy call
  const proxyCall = api.tx.Proxy.proxy({
    real: MultiAddress.Id('15r3tauLe4n8pRb9EzNVvdzbKc15rjscW8z2rzTRBGPwU4wh'),
    force_proxy_type: undefined,
    call: batchCall.decodedCall
  });

  console.log("Finding vanity TX...");
  const finalCall = proxyCall;//await findVanity(api, proxyCall);

  // Sign and send the extrinsic
  try {
    const encoded = (await finalCall.getEncodedData()).asHex();
    console.log(`Sending transaction: ${encoded}`);
    const result = await finalCall.signAndSubmit(signer);
	  console.log(`Transaction included in block ${result.block.hash}`);
  } catch (error) {
    console.error(`Transaction failed: ${error}`);
  }
}

// Tries to find a TX with at least 2 leading zero bytes
async function findVanity(api, tx) {
  // got into the ../tx-vanity-hash folder and do `cargo run --release -- txData`
  const encoded = (await tx.getEncodedData()).asHex().replace('0x', '');
  const execPromise = util.promisify(exec);

  const { stdout } = await execPromise(`cd ../tx-vanity-hash && cargo run --release --frozen -- ${encoded}`);

  // extract the line with `Fuzzed input: 0x..` and get the hex string
  const match = stdout.match(/Fuzzed input: (0x[0-9a-fA-F]+)/);
  if (!match) {
    console.error("Error: Vanity TX not found");
    process.exit(1);
  }
  let data = fromHex(match[1]);

  return api.txFromCallData(Binary.fromBytes(data));
}

main().catch(console.error).finally(() => process.exit());
