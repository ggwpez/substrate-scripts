import os
import json
import math

import numpy as np
import matplotlib.pyplot as plt

from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

data = []

PATH = "block-fee-mult.json"

if os.path.exists(PATH):
	with open(PATH, 'r') as f:
		data = json.load(f)
else:
	chain = SubstrateInterface(
		##url="wss://polkadot-asset-hub-rpc.polkadot.io",
		url="wss://polkadot.rpc.robonomics.network:443",
	)
	print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

	# Query the NextFeeMultiplier of the last 1000 blocks with 10 blocks in between
	header = chain.get_block_header()['header']
	number = header['number']

	for i in range(10):
		number -= 10000
		header = chain.get_block_header(block_number=number)['header']
		block_hash = header['hash']
		block_number = header['number']

		# Query the NextFeeMultiplier
		try:
			multiplier = chain.query("TransactionPayment", "NextFeeMultiplier", [], block_hash=block_hash)
		except SubstrateRequestException as e:
			print(f"Failed to query NextFeeMultiplier: {e}")
			break

		print(f"[{block_number}] NextFeeMultiplier: {multiplier}")
		data.append((block_number, multiplier.value))

	# Write to json
	with open(PATH, 'w') as f:
		json.dump(data, f, indent=4)

x = [d[0] for d in data]
y = [(d[1] / 1e18) for d in data]

# Plot as normal graph
plt.plot(x, y)
plt.xlabel("Block number")
plt.ylabel("Fee price multiplier [lg]")
plt.title("Log scale fee price per block")
plt.yscale('log')
plt.show()

# prepare data for heat map
#w = int(math.sqrt(len(x)))
#h = int(len(x) / w)
#Y = np.array(y[:w*h]).reshape(w, h)

#plt.title("Fee price per block % compared to baseline")
#plt.imshow(Y,  interpolation='nearest')
#plt.xticks([])
#plt.yticks([])
#plt.colorbar()
#plt.show()
