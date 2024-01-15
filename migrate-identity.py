"""
SPDX-License-Identifier: GPL-3.0-only

This script runs a lazy migration on the preimage pallet for:
	<https://github.com/paritytech/polkadot-sdk/pull/1814>

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
	#url="ws://127.0.0.1:9944",
	# Using the public endpoint can get you rate-limited.
	# url="wss://kusama-rpc.polkadot.io",
	# These Parity internals are not limited.
	url="wss://rococo-public-rpc.blockops.network/ws"
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

sender_uri = os.getenv('SENDER_URI', '//Alice')
sender = Keypair.create_from_uri(sender_uri)
print(f"Using sender account {sender.ss58_address}")

weight_second = 1e12
decimals = chain.token_decimals or 0

def main():
	while True:
		unmigrated = identities(BATCH_SIZE)
		if len(unmigrated) == 0:
			print("No identities to migrate - finish")
			return

		print(f"Migrating {len(unmigrated)} identities")

		batch = []
		for (i, user) in enumerate(unmigrated):
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
def identities(page_size):
	print(f'Fetching the next {page_size} identities to be migrated')
	query = chain.query_map('Identity', 'IdentityOf', page_size=page_size)

	accs = []
	for (account, data) in query:
		if len(accs) == page_size:
			break
		accs.append(account.value)
	return accs

if __name__ == "__main__":
	main()
