"""

Setup a venv and install the substrate-interface:

```bash
python3 -m venv venv
venv/bin/pip install substrate-interface
```

Now add a cron job to run every hour to check for votable referenda. You need to:
- Replace the path to the substrate-scripts folder with an absolute path.
- Replace the account address with your own.
- Add tracks that you can vote on. The tracks below are for Rank 3 fellows.

0 * * * * cd REPLACE_ME/substrate-scripts && venv/bin/python3 votable.py 16a357f5Sxab3V2ne4emGQvqJaCLeYpTMx3TCjnQhmJQ71DX --tracks 1 2 3 11 21
"""

import os
import json
import math
import time
import argparse

from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

def main():
	parser = argparse.ArgumentParser(description='List votable referenda')
	parser.add_argument('account', help='The account to check')
	parser.add_argument('--tracks', help='The tracks to check', nargs='+', default=[])
	args = parser.parse_args()
	tracks = [int(t) for t in args.tracks]
	ACC = args.account

	if len(tracks) == 0:
		print("Please specify the tracks to check with --tracks")
		exit(1)

	chain = SubstrateInterface(
		url="wss://polkadot-collectives-rpc.polkadot.io",
		#url="ws://127.0.0.1:8000",
	)
	print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

	good_state = ['DecisionDepositPlaced', 'Ongoing', 'Submitted', 'DecisionStarted', 'ConfirmStarted']

	ongoing = []

	# List all referenda
	referenda = chain.query_map("FellowshipReferenda", "ReferendumInfoFor")
	referenda_by_index = {}
	for index, ref in referenda:
		ref = ref.value
		index = index.value
		
		status = list(ref.keys())[0]
		if not status in good_state:
			continue
		
		ongoing.append(index)
		referenda_by_index[index] = ref[status]

	# Now get all referenda from the collective pallet:
	voted = chain.query_map("FellowshipCollective", "Voting")
	for (index, account), vote in voted:
		if not index in ongoing:
			continue
		
		if account == ACC:
			ongoing.remove(index)

	can_vote = []
	for i in ongoing:
		origin = referenda_by_index[i]['origin']['FellowshipOrigins']
		track = referenda_by_index[i]['track']

		if track in tracks:
			print(f"[ {origin} ] Please vote on https://collectives.subsquare.io/fellowship/referenda/{i}")
			can_vote.append(i)

	if len(can_vote) == 0:
		print("No referenda to vote on")
	else:
		found = len(can_vote)
		print(f"Found {found} referenda to vote on")
		as_str = ", ".join([str(i) for i in can_vote])
		os.system(f"osascript -e 'display notification \"Please vote on referenda: {as_str}\" with title \"New Fellowship Referenda\" sound name \"Submarine\"'")

if __name__ == "__main__":
	main()
