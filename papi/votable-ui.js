import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { exec } from 'child_process';
import util from "node:util";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const port = 8080;

let referenda = [];
let votes = {};

app.use(express.json());

app.get('/', (req, res) => {
  res.sendFile(join(__dirname, 'voting.html'));
});

app.get('/referenda', (req, res) => {
  res.json(referenda);
});

app.post('/vote', (req, res) => {
  const { refIndex, vote } = req.body;
  votes[refIndex] = vote;
  res.sendStatus(200);
});

app.get('/finish', async (req, res) => {
  var ayes = [];
  var nays = [];

  for (const [key, vote] of Object.entries(votes)) {
    if (vote === 'Aye') {
      ayes.push(key);
    } else {
      nays.push(key);
    }
  }

  if (ayes.length === 0 && nays.length === 0) {
    res.send("No votes staged");
    return;
  }

  var ayeStr = "";
  if (ayes.length > 0) {
    ayeStr = `--ayes ${ayes.join(" ")}`;
  }
  var nayStr = "";
  if (nays.length > 0) {
    nayStr = `--nays ${nays.join(" ")}`;
  }

  const command = `node batch-vote.js ${ayeStr} ${nayStr}`;
  console.log(`Executing: ${command}`);

  const execPromise = util.promisify(exec);
  await execPromise(command);
  process.exit(0);
});

export function startVotingServer(referendaToVote) {
  referenda = referendaToVote;
  app.listen(port, () => {
    console.log(`Voting server running at http://localhost:${port}`);
    console.log('Open this URL in your browser to start voting');
  });
}
