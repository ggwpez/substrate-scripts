"""
SPDX-License-Identifier: GPL-3.0-only

This script runs migration for the identity pallet for:
	<https://github.com/paritytech/polkadot-sdk/pull/1814>

Install the dependency:
	pip install substrate-interface
Set the env variable `SENDER_URI` and run:
	python3 migrate-identity.py
"""

"""
The batch size for each call to `reap_identity`.
It is set to a small value such that in case of a bug, the script wont burn
through a lot of funds.
"""
BATCH_SIZE = 16

import json
import os
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

chain = SubstrateInterface(
	#url="ws://127.0.0.1:9944",
	# Using the public endpoint can get you rate-limited.
	# url="wss://kusama-rpc.polkadot.io",
	# Or use some external node:
	url="wss://rococo-try-runtime-node.parity-chains.parity.io:443"
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

sender_uri = os.getenv('SENDER_URI', '//Alice')
sender = Keypair.create_from_uri(sender_uri)
print(f"Using sender account {sender.ss58_address}")

weight_second = 1e12
decimals = chain.token_decimals or 0

def main():
	unmigrated = identities()
	if len(unmigrated) == 0:
		print("No identities to migrate - finish")
		return

	print(f"Migrating {len(unmigrated)} identities")

	for chunk in chunks(unmigrated, BATCH_SIZE):
		batch = []

		for user in chunk:
			batch.append(chain.compose_call(
				call_module='IdentityMigrator',
				call_function='reap_identity',
				call_params={
					'who': user,
				}
			))
			print(f' - {user}')

		call = chain.compose_call(
			call_module='Utility',
			call_function='batch',
			call_params={
				'calls': batch,
			}
		)
		extrinsic = chain.create_signed_extrinsic(call=call, keypair=sender)
		print(f'Sending {len(batch)} batched calls in extrinsic {extrinsic.hash}')

		try:
			receipt = chain.submit_extrinsic(extrinsic, wait_for_inclusion=True)
			print(f"Extrinsic included in block {receipt.block_hash}: "
				f"consumed {receipt.weight['ref_time'] / weight_second} seconds of weight and "
				f"paid {(receipt.total_fee_amount or 0) / 10**decimals} {chain.token_symbol}")
			if receipt.total_fee_amount > 0:
				raise Exception("Fee payed 😱")
		except SubstrateRequestException as e:
			print(f"Failed to submit extrinsic: {e}")
			raise e

# Get the next `page_size` identities to be migrated.
def identities():
	print(f'Fetching the identities to be migrated')
	query = chain.query_map('Identity', 'IdentityOf')

	accs = []
	for (account, data) in query:
		accs.append(account.value)
	return accs

def chunks(list, n):
	"""
	Lazily split 'list' into 'n'-sized chunks.
	"""
	for i in range(0, len(list), n):
		yield list[i:i + n]


if __name__ == "__main__":
	main()
