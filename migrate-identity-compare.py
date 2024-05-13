"""
SPDX-License-Identifier: GPL-3.0-only

Compare that the Kusama identity pallet's storage `IdentityOf` is the same as the Kusama Collective chain.
"""

import json
import os
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

chain = SubstrateInterface(
	url="wss://kusama-rpc.polkadot.io"
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

ksm = {}
query = chain.query_map('Identity', 'IdentityOf')
for acc, i in query:
	ksm[acc.value] = i.value

chain = SubstrateInterface(
	url="wss://kusama-rpc.dwellir.com"
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

collectives = {}
query = chain.query_map('Identity', 'IdentityOf')
for acc, i in query:
	collectives[acc.value] = i.value

# Sort and compare
ksm = dict(sorted(ksm.items()))
collectives = dict(sorted(collectives.items()))

with open("ksm.json", "w") as f:
	json.dump(ksm, f)
with open("collectives.json", "w") as f:
	json.dump(collectives, f)
print("Wrote Kusama and collectives identity pallets to files.")

if ksm != collectives:
	raise Exception("Kusama and collectives identity pallets are different.")
