import argparse
import os

from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

parser = argparse.ArgumentParser(description='Retain a fellow')
parser.add_argument('fellow', help='The address to retain') 
address = parser.parse_args().fellow

# Connect to collectives chain


substrate = SubstrateInterface(
	url="wss://rpc-collectives-polkadot.luckyfriday.io"
)

# Query the FellowshipCollectives pallet for the rank:
query = substrate.query("FellowshipCollective", "Members", params=[address])
rank = query.value['rank']
print(f'Retaining {address} at rank {rank}')

# Construct the FellowshipCore::Approve call
approve_call = substrate.compose_call(
	call_module='FellowshipCore',
	call_function='approve',
	call_params={
		'who': address,
		'at_rank': rank
	}
)
hex_encoded = approve_call.encode()

referenda_call = substrate.compose_call(
	call_module='FellowshipReferenda',
	call_function='submit',
	call_params={
		'proposal_origin': { 'FellowshipOrigins': f'RetainAt{rank}Dan' },
		'proposal': { 'Inline': f'{hex_encoded}' },
		'enactment_moment': { 'At': 1 }
	}
)

print(f'https://polkadot.js.org/apps/?rpc=wss%3A%2F%2Fsys.ibp.network%2Fcollectives-polkadot#/extrinsics/decode/{referenda_call.encode()}')
