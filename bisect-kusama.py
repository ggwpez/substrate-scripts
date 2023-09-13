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

# Convert a accountId to ss58
def to_ss58(id):
	return chain.ss58_encode(id)

def ss58_to_id(ss58):
	return "0x" + chain.ss58_decode(ss58)

acc = to_ss58("0xcbb919d989fe3db6c51a99b3e815cc87420183611af15bb9bbf2a5796d0d2d6f") #"FFMUJRo3YWJzYo4PwzqAAsvdSS1NpD4GyzVfoWHLDE5jkpC" #"0x037a8e00a50bc1c33d6e5bbe743128e028b354a0aaf56a0e589331f1219c7210"
print(f"Checking account {acc}")

def predicate2(block):
	hash = chain.get_block_hash(block)
	query = chain.query('System', 'Account', params=[acc], block_hash=hash)
	free = query.value['data']['free']
	print(f"Checking block {block}: {free}")
	return free > 0

def predicate(block):
	hash = chain.get_block_hash(block)
	query = chain.query_multi(["0xc2261276cc9d1f8598ea4b6a74b15c2f218f26c73add634897550b4003b26bc6de1e86a9a8c739864cf3cc5ec2bea59fd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d"], block_hash=hash)
	print(f"Checking block {block}: {query.value}")
	return query.value is not None

# do binary search
def search(start, end):
	if start == end:
		# double check
		if not predicate(start):
			raise Exception("Predicate failed")
		print(f"|-> {start} <-|")
		return start

	mid = (start + end) // 2
	if predicate(mid):
		return search(start, mid)
	else:
		return search(mid + 1, end)

last = chain.get_chain_head()
last_num = chain.get_block_number(last)
search(1, last_num)
