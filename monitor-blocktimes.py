import os
import json

import numpy as np
import matplotlib.pyplot as plt

from substrateinterface import SubstrateInterface

def fetch(n):
	substrate = SubstrateInterface(
		url="wss://polkadot-try-runtime-node.parity-chains.parity.io:443",
	)
	current = substrate.get_block_header()
	number = current["header"]["number"]

	timestamps = {}
	for block in range(number - n, number):
		# Get the block header
		header = substrate.get_block_header(block_number=block)
		# Query the timestamp
		timestamp = substrate.query(
			module="Timestamp",
			storage_function="Now",
			block_hash=header["header"]["hash"],
		)
		timestamp = timestamp.value / 1000
		# Print the timestamp
		print(f"Block {block} has timestamp {timestamp}")
		timestamps[block] = timestamp
	# Save the timestamps
	with open("timestamps.json", "w") as file:
		file.write(json.dumps(timestamps))
	return timestamps	

def fetch_or_load(n):
	# check if json file exists
	if os.path.isfile("timestamps.json"):
		# load the file
		with open("timestamps.json", "r") as file:
			data = file.read()
			timestamps = json.loads(data)
		# check if the file is complete
		if len(timestamps) == n:
			return timestamps
	return fetch(n)

# Load the last hour
n = 600
timestamps = fetch_or_load(n)
# parse as int, int map
timestamps = {int(k): int(v) for k, v in timestamps.items()}
# lowest
lowest = min(timestamps.keys())

# Plot the timestamps

# Calculate the diff to the previous block
diffs = {}
for i in range(lowest + 1, lowest + n):
	diffs[i] = timestamps[i] - timestamps[i-1]

# Plot the diffs
plt.plot(list(diffs.keys()), list(diffs.values()))
# Draw a green line at 6 seconds
plt.axhline(y=6, color='g', linestyle='-')
# Draw a red line at 12 seconds
plt.axhline(y=12, color='r', linestyle='-')
# Add a legend for both lines
plt.legend(["Blocktime", "6 seconds", "12 seconds"])
# X xis label
plt.xlabel("Block number")
# Y axis label
plt.ylabel("Blocktime diff [s]")
# Set a title
plt.title("Blocktime diff of the last hour")
plt.show()
