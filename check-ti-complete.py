'''
Verifies the integrity of the `TotalIssuance` storage item in a FRAME runtime.

The script can either check the TI at a specific block number, or bisect a range of block number to
find the block number that invalidated the TI.

Since the querying of all accounts is slow, the script writes all successfully queried blocks to a
file `blocks-ti.txt`.

# Usage

Checking a single block looks like this:
```
python3 check-ti-complete.py --url wss://rpc.polkadot.io block 123456
```

Here we find the first block that had incorrect TI offset of 42:
```
python3 check-ti-complete.py --url wss://rpc.polkadot.io bisect 10000 20000 --offset 42
```

Subsequently, these offsets can be adjusted via https://github.com/paritytech/polkadot-sdk/pull/3001
'''

import json
import os
import sys
import argparse

from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

decimals = 0

def connect(url):
	chain = SubstrateInterface(url)

	print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")
	global decimals
	decimals = chain.token_decimals
	global unit
	unit = chain.token_symbol
	print("Decimals", decimals)
	return chain

def dot(v):
	return f"{v/10**decimals:,} {unit}"

def check_block(chain, block, expected_diff, trace=False):
	at = chain.get_block_hash(block)

	ti = chain.query("Balances", "TotalIssuance", block_hash=at).value
	print(f"TI at {block}: {dot(ti)}")

	all_accounts = {}
	sum = 0
	c = 0
	accounts = chain.query_map("System", "Account", block_hash=at, page_size=1000)
	for id, data in accounts:
		id = id.value
		data = data["data"]
		free = data["free"].value
		reserved = data["reserved"].value
		total = free + reserved
		sum += total

		if trace:
			all_accounts[id] = {
				"free": free,
				"reserved": reserved,
				"total": total,
			}

		c += 1
		if c % 1000 == 0:
			print(f"[{block}] Processed {c} accounts")

	print(f"[{block}] Queried {c} accounts in total")

	if ti < sum:
		print(f"[{block}] The TotalIssuance is smaller than the sum of all accounts TI. TI: {dot(ti)}, Sum: {dot(sum)}")
		print(f"[{block}] TI must be increased by {ti} - {sum} = {ti - sum} {dot(ti - sum)}")
	elif ti > sum:
		print(f"[{block}] The TotalIssuance is larger than the sum of all accounts TI. TI: {dot(ti)}, Sum: {dot(sum)}")
		print(f"[{block}] TI must be decreased by {sum} - {ti} = {sum - ti} {dot(sum - ti)}")
	else:
		print(f"[{block}] The TotalIssuance is equal to the sum of all accounts TI. TI: {dot(ti)}")
	
	with open(f"all-accounts-{chain.chain}-{block}.txt", "a") as f:
		f.write(json.dumps(all_accounts) + "\n")
	with open("blocks-ti.json", "a") as f:
		obj = {
			"block": block,
			"sum": sum,
			"ti": ti,
			"runtime": chain.chain,
		}
		if ti != sum:
			obj["diff"] = ti - sum
		f.write(json.dumps(obj) + "\n")

	ret = ((ti - sum) == expected_diff)
	if ret:
		print(f"[{block}] The difference is as expected")
	else:
		print(f"[{block}] The difference is not as expected")
	return ret

def check_range(chain, start, end, expected_diff):
	if start == end:
		return start
	
	mid = (start + end) // 2
	if check_block(chain, mid, expected_diff):
		return check_range(chain, start, mid, expected_diff)
	else:
		return check_range(chain, mid+1, end, expected_diff)

def parse_args():
	parser = argparse.ArgumentParser(description="Check TotalIssuance")
	parser.add_argument("--url", type=str, default="wss://rpc.polkadot.io", help="URL of the node to connect to")
	# Two sub-command options: block and bisect
	subparsers = parser.add_subparsers(dest="subcommand", required=True)

	# Block sub-command
	block_parser = subparsers.add_parser("block", help="Check a specific block")
	block_parser.add_argument("block", type=int, help="Block number to check")
	block_parser.add_argument("--trace", help="Store complete trace", action="store_true")

	# Bisect sub-command
	bisect_parser = subparsers.add_parser("bisect", help="Bisect the range")
	bisect_parser.add_argument("start", type=int, help="Start block number")
	bisect_parser.add_argument("end", type=int, help="End block number")
	bisect_parser.add_argument("--offset", type=int, help="Expected difference")

	return parser.parse_args()

if __name__ == "__main__":
	args = parse_args()
	chain = connect(args.url)

	if args.subcommand == "block":
		check_block(chain, args.block, 0, args.trace)
	elif args.subcommand == "bisect":
		check_range(chain, args.start, args.end, args.offset)
	else:
		raise Exception("Unknown subcommand")
