import json
import os
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

chain = SubstrateInterface(
	#url="ws://127.0.0.1:9944",
	# Using the public endpoint can get you rate-limited.
	url="wss://kusama-rpc.polkadot.io",
	# These Parity internals are not limited.
	# url="wss://polkadot-try-runtime-node.parity-chains.parity.io:443"
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

# Try to query either as value or map
def try_query(f):
	try:
		return try_query_map(f)
	except Exception as e:
		try:
			return try_query_value(f)
		except Exception as e:
			raise Exception(f"Could not query {f.module_name}::{f.storage_name} as value or map")

def try_query_value(f):
	query = chain.query(f.module_name, f.storage_name)

	yield ("key", query.value)

def try_query_map(f):
	query = chain.query_map(f.module_name, f.storage_name, page_size=1000)

	for (i, (key, value)) in enumerate(query):
		yield (key, value)

functions = chain.get_metadata_storage_functions()
# Map to dict
functions = {type('new_dict', (object,), f): f for f in functions}
functions = sorted(functions, key=lambda f: f.module_name + f.storage_name)
broken = []

for f in functions:
	if f.module_prefix != "Balances":
		continue
	print(f"{f.module_prefix}::{f.storage_name}")
	query = try_query(f)

	# Try to query as map:
	try:
		good = 0
		bad = 0
		heuristic = False

		for (i, (key, value)) in enumerate(query):
			if i % 5000 == 0 and i > 0:
				print(f"  {f.module_name}::{f.storage_name}: good: {good}, bad: {bad}")

			if value is None:
				bad += 1
				print("Bad key", key)
			else:
				good += 1

			if i > 5000 and bad == 0:
				heuristic = True
				break
		
		if bad > 0:
			print(f"  💔 {f.module_name}::{f.storage_name}: good: {good}, bad: {bad} [BROKEN]")
			broken.append([f, good, bad])
		elif heuristic:
			print(f"  🤷 {f.module_name}::{f.storage_name}: good: {good}, bad: {bad}")
		else:
			print(f"  ✅ {f.module_name}::{f.storage_name}: good: {good}, bad: {bad}")
	except Exception as e:
		print(f"  🦘 Error querying as map: {e}")

if len(broken) > 0:
	print(f"Found {len(broken)} broken storage items:")
	for (f, good, bad) in broken:
		print(f"  {f.module_name}::{f.storage_name}: good: {good}, bad: {bad}")
