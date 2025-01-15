# query all Preimage::StatusFor and print the accounts

import json
import os
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

chain = SubstrateInterface(
	#url="ws://127.0.0.1:9944",
	# Using the public endpoint can get you rate-limited.
	url="wss://rpc.polkadot.io",
	# These Parity internals are not limited.
	# url="wss://polkadot-try-runtime-node.parity-chains.parity.io:443"
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

accounts = []
# query all Preimage::StatusFor and print the accounts
query = chain.query_map("Preimage", "StatusFor", page_size=1000)
for (key, value) in query:
	v = value.value
	if 'Unrequested' in v:
		acc = v['Unrequested']['deposit'][0]
		balance = int(v['Unrequested']['deposit'][1])
		accounts.append((acc, balance))

# Sort by balance
accounts.sort(key=lambda x: x[1], reverse=True)

for acc, balance in accounts:
	print(f"- `{acc}`: {balance / 10**10} DOT")

print(f"Affected accounts: {len(accounts)}")
