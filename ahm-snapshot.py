# query all Preimage::StatusFor and print the accounts

import time

from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

RC_RPC_URL = "wss://kusama-rpc.polkadot.io:443"
AH_RPC_URL = "wss://kusama-asset-hub-rpc.polkadot.io:443"

ah = SubstrateInterface(
	url=AH_RPC_URL,
	# Using the public endpoint can get you rate-limited.
	#url="wss://polkadot-asset-hub-rpc.polkadot.io",
	# These Parity internals are not limited.
	# url="wss://polkadot-try-runtime-node.parity-chains.parity.io:443"
)

print(f"Connected to {ah.name}: {ah.chain} v{ah.version}")

ah_block_hash = ah.get_chain_finalised_head()
print(f"Using Asset Hub block hash: {ah_block_hash}")

# Get the block
block = ah.get_block(ah_block_hash)

validation_data = None
# Read the inherents
for extrinsic in block['extrinsics']:
    if extrinsic['call']['call_function']['name'] == 'set_validation_data':
        validation_data = extrinsic
        break

if validation_data is None:
    print("No validation data found in Asset Hub block")
    exit(1)

parent_number = validation_data['call']['call_args'][0]['value']['validation_data']['relay_parent_number'].value
print(f"Relay block number: {parent_number}")

# Connect to the Relay Chain
relay = SubstrateInterface(
	url=RC_RPC_URL,
    #url="wss://rpc.polkadot.io",
)

attempts = 10
rc_block_hash = None

while True:
	rc_block_hash = relay.get_block_hash(parent_number)
	print(f"Relay block hash: {rc_block_hash}")
	attempts -= 1
    
	if attempts == 0 or rc_block_hash:
		break
	time.sleep(3)

if rc_block_hash is None:
	print("Failed to get relay block hash")
	exit(1)

print(f"Commands:\ntry-runtime create-snapshot --uri {RC_RPC_URL} kusama.snap --at {rc_block_hash}")
print(f"try-runtime create-snapshot --uri {AH_RPC_URL} ah-kusama.snap --at {ah_block_hash}")
