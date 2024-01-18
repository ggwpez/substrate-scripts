# Find issues with the TotalIssuance

import json
import os
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

chain = SubstrateInterface(
	#url="ws://127.0.0.1:9944",
	# Using the public endpoint can get you rate-limited.
	#url="wss://rpc.polkadot.io",
	url="wss://rpc.ibp.network/polkadot",
	# Or use some external node:
	#url="wss://rococo-try-runtime-node.parity-chains.parity.io:443"
)

# open a file to write the results to
f = open("ti-issues.txt", "a")

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")
decimals = chain.token_decimals or 10

#hash = chain.get_chain_finalised_head()
#header = chain.get_block_header(block_hash=hash)
num = 19074056 #header['header']['number']

accs = 0
hits = 0
cache = {}
if os.path.exists("ti-cache.json"):
	with open("ti-cache.json", "r") as cache_file:
		cache = json.load(cache_file)
		print(f"Loaded {len(cache)} TI values from cache")

def get_ti(num):
	global accs, hits
	accs += 1
	if num in cache:
		hits += 1
		print(f"Cache hit rate {100*hits/accs} % for {accs} accesses")
		return cache[num]
	
	hash = chain.get_block_hash(num)
	ti = int(chain.query("Balances", "TotalIssuance", block_hash=hash).value)

	cache[num] = ti
	if len(cache) % 100 == 0:
		with open("ti-cache.json", "w") as cache_file:
			json.dump(cache, cache_file)
	return ti

def locate(start, end):
	print(f"Locating TI change between {start} and {end}")
	if start >= end or get_ti(start) == get_ti(end):
		return store(start)
	
	mid = (start + end) // 2
	ti = get_ti(mid)

	if ti == get_ti(end):
		return locate(start, mid)
	else:
		return locate(mid+1, end)

def store(block):
	f.write(f"{block}\n")
	f.flush()
	return block

def find_all(start, end):
	found = locate(start, end)
	
	while found != start:
		found = locate(start, found-1)

def jump_search(start, end, jump_size):
	cursor = end
	while cursor > start:
		print(f"Jumping from {cursor} to {cursor-jump_size}")
		find_all(cursor-jump_size, cursor)
		cursor -= jump_size
		
jump_search(0, num, 64)
print("Done")
f.close()

#I am not sure if its enough to look for balance change events, i think it rather needs to look into storage.  
# Currently i am doing a binary search to find all blocks where the TI changed, then as next i will try to see if that always matches the expectation
