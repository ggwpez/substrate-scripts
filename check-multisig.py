# Prints the number of empty agendas of the Kusama scheduler.

# Output from 20.12.2022, 15:57 (CET)
#
# Block height 15500000 has 604 empty agendas
# Block height 15550000 has 1008 empty agendas
# Block height 15600000 has 1397 empty agendas
# Block height 15650000 has 2180 empty agendas
# Block height 15700000 has 2723 empty agendas
# Block height 15750000 has 2989 empty agendas
# Block height 15800000 has 3554 empty agendas
# Block height 15829813 has 3690 empty agendas
# Average growth rate: 5.61 / h, 134.74 / d

from substrateinterface import SubstrateInterface

substrate = SubstrateInterface(
    url="wss://rococo-rpc.polkadot.io",
)

query = substrate.query_map(
	module='Multisig',
	storage_function='Multisigs',
	page_size=1000, 
	params= ["5FRz8z6U87LBXLUuBRRy4JtVAh2jhkDSbR5ntCGM2Ds631dJ"])

for block, multisig in query:
	print(f"Block height {block} has {multisig}")
