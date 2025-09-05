from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

chain = SubstrateInterface(
	url="wss://pas-rpc.stakeworld.io",
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

# Fetch block hash for 
header = chain.get_block_header("0x6a2993bf952925f445158e9018f59d347bf35c5018851d6d713d860847cc433c")['header']
number = header['number']

# Read the DMP queue (1111) of each block and go up to parent for 1000 blocks
for i in range(1000):
	block_hash = chain.get_block_hash(number)

	storage_keys = [chain.create_storage_key('Dmp', 'DownwardMessageQueues', [1000])]
	query = chain.query_multi(storage_keys, block_hash=block_hash)
	num_msgs = 0
	for (key, value) in query:
		num_msgs += len(value)
	suffix = "!!" if num_msgs > 80 else ("!" if num_msgs > 50 else "")
	print(f"#{number} Block hash: {block_hash} {num_msgs} {suffix}")

	number -= 1
