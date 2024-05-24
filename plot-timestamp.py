import os
import json
import math
import datetime

import numpy as np
import matplotlib.pyplot as plt

from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

START = 20803735 # 2024-05-17 00:00:00
QUERIES  = 3650 # How many times to query
DIFF     = 1440 # How many blocks to skip in between each query
EXPECTED = 6 * 1000 # Expected block time in ms

data = []
PATH = "block-time-polkadot.json"

if os.path.exists(PATH):
	with open(PATH, 'r') as f:
		data = json.load(f)

chain = SubstrateInterface(
	url="wss://rpc.polkadot.io",
)
print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

for i in range(QUERIES+1):
	block_number = START - i * DIFF

	if any(d[0] == block_number for d in data):
		continue

	print(f"Querying block {block_number}")
	block_hash = chain.get_block_hash(block_number)

	try:
		now = chain.query("Timestamp", "Now", [], block_hash=block_hash)
	except SubstrateRequestException as e:
		print(f"Failed to timestamp: {e}")
		break

	print(f"[{block_number}] Timestamp: {now}, hash: {block_hash}")
	data.append((block_number, now.value))

# Write to json
with open(PATH, 'w') as f:
	json.dump(data, f, indent=4)

# Sort by block number
data = sorted(data, key=lambda x: x[0])
# only take take last QUERIES (in case that we have cached)
#data = data[-(QUERIES + 1):]

expected_y = [data[0][1] + EXPECTED * DIFF * i for i in range(len(data))]

x = [d[0] - data[0][0] for d in data]
x = [d / (3600 * 24 * 1000 / EXPECTED) for d in x]
y = [d[1] for d in data]

diff_y = [expected_y[i] - y[i] for i in range(len(y))]
diff_y = [(d / 1000) / (3600 * 24) for d in diff_y]

# Print first and last timestamp in human readable format
print(f"First timestamp: {datetime.datetime.fromtimestamp(data[0][1] / 1000)} at block {data[0][0]}")
print(f"Last  timestamp: {datetime.datetime.fromtimestamp(data[-1][1] / 1000)} at block {data[-1][0]}")
print(f"Difference in days: {(data[-1][1] - data[0][1]) / (1000 * 3600 * 24)}")

plt.title("Polkadot Relay Clock Skew")
plt.plot(x, diff_y, label="Difference")
plt.xlabel("Time in multiple of 14400 blocks (should be 24 hrs)")
plt.ylabel("Difference (days)")
plt.legend()
plt.show()
