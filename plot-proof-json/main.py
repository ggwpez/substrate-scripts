# Shitty script to plot the output of `--json-file` from FRAME benchmarking CLI.
# Usage: python3 main.py <json-file>

import numpy as np
import matplotlib.pyplot as plt
import json
import sys

if len(sys.argv) != 2:
	raise Exception('Expected a JSON file as argument')
# Read the data from raw.json
with open(sys.argv[1]) as f:
	data = json.load(f)

if len(data) != 1:
	raise Exception('Expected exactly one data point')

data = data[0]
print(f'Plotting {data["pallet"]}::{data["benchmark"]}')

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
x = []
y = []
z = []
w = []

for d in data['db_results']:
	cs = d['components']
	x.append(cs[0][1])
	y.append(cs[1][1])
	z.append(cs[2][1])
	w.append(d['proof_size'])
	print(f'({cs[0][1]}, {cs[1][1]}, {cs[2][1]}) -> {d["proof_size"]}')

img = ax.scatter(x, y, z, c=w, cmap=plt.hot())
# put axis labels
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
fig.colorbar(img)
plt.show()
