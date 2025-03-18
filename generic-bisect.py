"""
Generic bisection script to find storage changes in a Substrate chain.

Example:

> python3 generic-bisect.py --url wss://rpc.polkadot.io bisect 24899778 2518733

Change the `predicate(chain, num)` function with something that you want to find. Should return True
if the predicate is met.

The other predicate functions are examples.
"""

import argparse

from substrateinterface import SubstrateInterface

decimals = 0

def connect(url):
	chain = SubstrateInterface(url)

	print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")
	global decimals
	decimals = 10
	print("Decimals", decimals)
	return chain

def dot(v):
	return f"{v/10**decimals:,} DOT"

def predicate_provider(acc, want_provider):
	def predicate(chain, num):
		at = chain.get_block_hash(num)
		print(f"Checking block {num} ({at})")

		query = chain.query('System', 'Account', params=[acc], block_hash=at)
		if 'providers' in query.value:
			providers = query.value['providers']
			print(f"Providers {providers}, want {want_provider}")
			return int(providers) == int(want_provider)
		else:
			print(f"Account {acc} has no providers: {query.value}")
			return False

	return predicate

def predicate_total_balance(acc, want_total_balance):
	def predicate(chain, num):
		at = chain.get_block_hash(num)
		print(f"Checking block {num} ({at})")

		query = chain.query('System', 'Account', params=[acc], block_hash=at)
		if 'free' in query.value['data'] and 'reserved' in query.value['data']:
			total = query.value['data']['free'] + query.value['data']['reserved']
			print(f"Total {total}, want {want_total_balance}")
			return int(total) < int(want_total_balance)
		else:
			print(f"Account {acc} has no free or reserved")
			return False

	return predicate

def predicate_reserved(acc, want_reserved):
	def predicate(chain, num):
		at = chain.get_block_hash(num)
		print(f"Checking block {num} ({at})")

		query = chain.query('System', 'Account', params=[acc], block_hash=at)
		if 'reserved' in query.value['data']:
			reserved = query.value['data']['reserved']
			print(f"Reserved {reserved}, want {want_reserved}")
			return int(reserved) == int(want_reserved)
		else:
			print(f"Account {acc} has no reserved")
			return False

	return predicate

def predicate(chain, num):
	return predicate_total_balance("15QBmCuy3aRxn8xuzfaRvzaLdawsGbPmttbcvBU8q71kEb7a", 700000000000)(chain, num)

def check_range(chain, start, end):
	if start == end:
		return start
	
	mid = (start + end) // 2
	if predicate(chain, mid):
		print(f" True")
		return check_range(chain, start, mid)
	else:
		print(f" False")
		return check_range(chain, mid+1, end)

def parse_args():
	parser = argparse.ArgumentParser(description="Check TotalIssuance")
	parser.add_argument("--url", type=str, default="wss://127.0.0.1:9955", help="Archive node")
	# Two sub-command options: block and bisect
	subparsers = parser.add_subparsers(dest="subcommand", required=True)

	# Block sub-command
	block_parser = subparsers.add_parser("block", help="Check a specific block")
	block_parser.add_argument("block", type=int, help="Block number to check")

	# Bisect sub-command
	bisect_parser = subparsers.add_parser("bisect", help="Bisect the range")
	bisect_parser.add_argument("start", type=int, help="Start block number")
	bisect_parser.add_argument("end", type=int, help="End block number")

	return parser.parse_args()

if __name__ == "__main__":
	args = parse_args()
	chain = connect(args.url)

	if args.subcommand == "block":
		predicate(chain, args.block)
	elif args.subcommand == "bisect":
		check_range(chain, args.start, args.end)
	else:
		raise Exception("Unknown subcommand")
