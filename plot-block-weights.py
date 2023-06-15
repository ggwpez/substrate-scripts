from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
import json

chain = SubstrateInterface(
    #url="ws://127.0.0.1:9944",
    # Using the public endpoint can get you rate-limited.
    url="wss://rpc.polkadot.io",
    # These Parity internals are not limited.
    #url="wss://polkadot-try-runtime-node.parity-chains.parity.io:443"
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")
begin = 15979502
end = 15980221

last  = end + 100
first = begin - 100

# Query the weight for each block
weights = {}

# Read from 'block-weights.json' if it exists
try:
	with open('block-weights.json', 'r') as f:
		weights = json.load(f)
except FileNotFoundError:
	first_hash = chain.get_block_hash(first)
	header = chain.get_block_header(block_number=last)['header']

	while header['parentHash'] != first_hash:
		i = header['number']
		# Access the state of `System.blockWeight`
		block_weight = chain.query(
			module='System',
			storage_function='BlockWeight',
			block_hash=header['hash']
		).value
		print(f"[{i}] Block weight {block_weight}")
		weights[i] = block_weight
		header = chain.get_block_header(header['parentHash'])['header']

# Sort by block number
weights = dict(sorted(weights.items(), key=lambda item: item[0]))

# Write to json
with open('block-weights.json', 'w') as f:
	json.dump(weights, f, indent=4)

block_limit = 2 * 10**12
normal = {}
operational = {}
mandatory = {}
total = {}

for block, weight in weights.items():
	normal[block] = (weight['normal']['ref_time'] / block_limit) * 100
	operational[block] = (weight['operational']['ref_time'] / block_limit) * 100
	mandatory[block] = (weight['mandatory']['ref_time'] / block_limit) * 100
	total[block] = normal[block] + operational[block] + mandatory[block]

# plot max total
max_total = max(total.values())
print(f"Max total: {max_total}")

# Now the plotting part
import matplotlib.pyplot as plt
import numpy as np

x = np.arange(first, last - 1)
plt.plot(x, total.values(), label="Total", color='#56F39A')
plt.plot(x, operational.values(), label="Operational", color='#D3FF33')
plt.plot(x, mandatory.values(), label="Mandatory", color='#E6007A')
plt.plot(x, normal.values(), label="Normal", color='#552BBF')

# Draw a red dotted vertical line at begin
plt.axvline(x=begin, color='#00B2FF', linestyle='--')
# .. and a blue one at end
plt.axvline(x=end, color='#00B2FF', linestyle='--')

plt.ylabel('Block weight (%)')
plt.xlabel('Block number')
plt.title(f"Ref-Time weights for Polkadot range {first} - {last} (dotted lines are migration start/end)")

plt.legend()
plt.show()
