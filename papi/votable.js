import { ApiPromise, WsProvider } from '@polkadot/api';
import { Command } from 'commander';
import { exec } from "child_process";
import { startVotingServer } from './votable-ui.js';
import https from 'https';
import dotenv from 'dotenv';

dotenv.config({ path: '../.env' });

async function didVote(refIndex, account) {
  const options = {
    method: 'POST',
    hostname: 'polkadot.api.subscan.io',
    path: '/api/scan/referenda/votes',
    headers: {
      'User-Agent': 'Apidog/1.0.0 (https://apidog.com)',
      'Content-Type': 'application/json',
      'X-API-Key': process.env.API_KEY
    }
  };

  const body = JSON.stringify({
    account: account,
    order: "asc",
    page: 0,
    referendum_index: refIndex,
    row: 10,
    sort: "conviction",
    valid: "valid"
  });

  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const votes = JSON.parse(data).data;
          if (votes.count == 0) {
            resolve(false);
          } else {
            resolve(true);
          }
        } catch (error) {
          reject(new Error('Error parsing JSON response'));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(body);
    req.end();
  });
}

async function main() {
  const program = new Command();
  program
    .argument('<account>', 'The account to check')
    .option('--tracks <tracks...>', 'The tracks to check', [])
    .option('--all-tracks', 'Check all tracks')
    .option('--rpc <string>', 'The RPC endpoint to connect to', 'wss://polkadot-collectives-rpc.polkadot.io')
    .option('--pallet <string>', 'The pallet to check', 'fellowshipReferenda')
    .parse(process.argv);

  const options = program.opts();
  const ACC = program.args[0];
  const tracks = options.tracks.map(Number);
  const allTracks = options.allTracks;

  if (tracks.length === 0 && !allTracks) {
    console.log("Please specify the tracks to check with --tracks or use --all-tracks");
    process.exit(1);
  }

  console.log(`Connecting to ${options.rpc}`);
  const wsProvider = new WsProvider(options.rpc);
  const api = await ApiPromise.create({ provider: wsProvider });

  console.log(`Connected to ${api.runtimeChain}: ${api.runtimeVersion.specName} v${api.runtimeVersion.specVersion}`);

  const goodStates = ['decisionDepositPlaced', 'ongoing', 'submitted', 'decisionStarted', 'confirmStarted'];

  let ongoing = [];
  const referendaByIndex = {};

  // List all referenda
  const referenda = await api.query[options.pallet].referendumInfoFor.entries();
  for (const [key, ref] of referenda) {
    const index = key.args[0].toNumber();
    const status = ref.value.toJSON();
    const statusKey = Object.keys(status)[0];

    if (!goodStates.includes(statusKey))
		continue;

    ongoing.push(index);
    referendaByIndex[index] = status[statusKey];
  }

  // Now get votes and filter out the ones that have already voted
  var canVote = [];
  for (const index of ongoing) {
    const voted = await didVote(index, ACC);

    if (!voted) {
      canVote.push(index);
      console.log(`You can vote on referendum ${index}`);
      if (canVote.length > 3)
        break;
    }
  }

  if (canVote.length === 0) {
    console.log("No referenda to vote on");
    process.exit(0);
  } else {
    // 30 minutes to vote
    setTimeout(function () {
      process.exit(0);
    }, 3 * 600000);
    const found = canVote.length;
    console.log(`Found ${found} referenda to vote on`);
    const asStr = canVote.join(", ");
    const plural = found === 1 ? "um" : "a";
    console.log(`Please vote on referend${plural}: ${asStr}`);
    exec(`osascript -e 'display notification "Please vote on ${found} OpenGov referend${plural}" with title "Votable referend${plural}"'`);
    
    startVotingServer(canVote);
  }

  await api.disconnect();
}

main()
