import json
import os
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

chain = SubstrateInterface(
	#url="ws://127.0.0.1:9944",
	# Using the public endpoint can get you rate-limited.
	#url="wss://kusama-rpc.polkadot.io",
	# These Parity internals are not limited.
	url="wss://rococo-try-runtime-node.parity-chains.parity.io:443"
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

holds = {}
query = chain.query_map("Balances", "Holds", page_size=1000)

for (acc, h) in query:
	holds[acc.value] = h.value

print(f"Found {len(holds)} holds")
json.dump(holds, open("holds.json", "w"), indent=2)

reserves = {}
query = chain.query_map("System", "Account", page_size=1000)

for (acc, a) in query:
	reserves[acc.value] = a['data']['reserved'].value

print(f"Found {len(reserves)} reserves")
json.dump(reserves, open("reserves.json", "w"), indent=2)

bad_account = []
for (acc, reserve) in reserves.items():
	reserve = 0 if reserve is None else reserve
	hold = 0 if acc not in holds else holds[acc]

	if reserve != hold:
		print(f"Account {acc} has {reserve} reserved but {hold} held")
		bad_account.append(acc)

print(f"Found {len(bad_account)} bad accounts")
json.dump(bad_account, open("bad-accounts.json", "w"), indent=2)
