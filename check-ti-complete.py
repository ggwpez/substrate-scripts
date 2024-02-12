# Find issues with the TotalIssuance

import json
import os
import sys
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

num=int(sys.argv[1])

chain = SubstrateInterface(
	#url="ws://127.0.0.1:9944",
	# Using the public endpoint can get you rate-limited.
	#url="wss://rpc.polkadot.io",
	url="wss://wss.api.moonbeam.network",
	# Or use some external node:
	#url="wss://rococo-try-runtime-node.parity-chains.parity.io:443"
)

# open a file to write the results to
f = open("ti-issues.txt", "a")

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")
decimals = 10
print("Decimals", decimals)

with open("sudo-blocks.json", "r") as f:
	extrinsics = json.load(f)

blocks = []
for ext in extrinsics:
	asdf = int(ext.split("-")[0])
	blocks.append(asdf)

blocks.sort()

def dot(v):
	return f"{v/10**decimals:,} DOT"

print(blocks)
#if os.path.exists("blocks-ti.txt"):
#	removed = 0
#	with open("blocks-ti.txt", "r") as f:
#		for line in f:
#			data = json.loads(line)
#			if not "diff" in data:
#				blocks.remove(data["block"])
#				removed += 1
#	print(f"Removed {removed} blocks from the list")

# query all accounts

def check_block(block):
	at = chain.get_block_hash(block)

	ti = chain.query("Balances", "TotalIssuance", block_hash=at).value
	print(f"TI at {block}: {dot(ti)}")

	sum = 0
	c = 0
	accounts = chain.query_map("System", "Account", block_hash=at, page_size=1000)
	for id, data in accounts:
		data = data["data"]
		free = data["free"].value
		reserved = data["reserved"].value
		total = free + reserved
		sum += total

		if c % 1000 == 0:
			print(f"[{block}] Processed {c} accounts")
		c += 1
	print(f"[{block}] Queried {c} accounts in total")

	if sum != ti:
		print(f"[{block}] TotalIssuance mismatch: {dot(sum)} vs {dot(ti)}")
		print(f"[{block}] Exact values: {sum} vs {ti}")
	else:
		print(f"[{block}] TotalIssuance matches: {dot(sum)}")
	
	with open("blocks-ti.txt", "a") as f:
		obj = {
			"block": block,
			"sum": sum,
			"ti": ti,
		}
		if ti != sum:
			obj["diff"] = ti - sum
		f.write(json.dumps(obj) + "\n")
	return ((ti - sum) == 0)

check_block(num)
sys._exit(0)

def check_range(start, end):
	if start == end:
		return start
	
	mid = (start + end) // 2
	if check_block(mid):
		return check_range(start, mid)
	else:
		return check_range(mid+1, end)

check_range(17051032, 19102065)
