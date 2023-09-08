"""
SPDX-License-Identifier: GPL-3.0-only

This script runs a lazy migration on the preimage pallet for:
	<https://github.com/paritytech/polkadot-sdk/pull/1363>

Install the dependency:
	pip install substrate-interface
Set the env variable `SENDER_URI` and run:
	python3 migrate-preimage-lazy.py
"""

"""
The batch size for each call to `ensure_updated`.
It is set to a small value such that in case of a bug, the script wont burn
through a lot of funds.
"""
BATCH_SIZE = 16

import json
import os
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

chain = SubstrateInterface(
	url="ws://127.0.0.1:9944",
	# Using the public endpoint can get you rate-limited.
	# url="wss://kusama-rpc.polkadot.io",
	# These Parity internals are not limited.
	# url="wss://polkadot-try-runtime-node.parity-chains.parity.io:443"
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

sender_uri = os.getenv('SENDER_URI', '//Alice')
sender = Keypair.create_from_uri(sender_uri)
print(f"Using sender account {sender.ss58_address}")

weight_second = 1e12
decimals = chain.token_decimals or 0

def main():
	head = chain.get_chain_head()
	unmigrated = preimages(head, False)
	migrated = preimages(head, True)
	total = len(unmigrated) + len(migrated)

	print(f"Total preimages {total} ({len(migrated)} migrated, {len(unmigrated)} unmigrated)")

	for (i, chunk) in enumerate(chunks(unmigrated, BATCH_SIZE)):
		call = chain.compose_call(
			call_module='Preimage',
			call_function='ensure_updated',
			call_params={
				'hashes': chunk,
			}
		)
		print(f"Transaction {i + 1}: upgrading {len(chunk)} preimages")

		try:
			receipt = chain.submit_extrinsic(
			extrinsic, wait_for_inclusion=True)
			print(f"Extrinsic included in block {receipt.block_hash}: "
				f"consumed {receipt.weight['ref_time'] / weight_second} seconds of weight and "
				f"paid {(receipt.total_fee_amount or 0) / 10**decimals} {chain.token_symbol}")
			if receipt.total_fee_amount > 0:
				raise Exception("Fee payed 😱")
		except SubstrateRequestException as e:
			print(f"Failed to submit extrinsic: {e}")
			raise e

def preimages(block, migrated):
	ret = []
	m = "RequestStatusFor" if migrated else "StatusFor"
	query = chain.query_map('Preimage', m, page_size=64, block_hash=block)

	for (hash, status) in query:
		ret.append(hash.value)
	
	return ret

def chunks(list, n):
	"""
	Lazily split 'list' into 'n'-sized chunks.
	"""
	for i in range(0, len(list), n):
		yield list[i:i + n]

if __name__ == "__main__":
	main()
