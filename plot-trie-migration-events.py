import os
import json
import math

import numpy as np
import matplotlib.pyplot as plt

PATH = "params.json"
with open(PATH, 'r') as f:
	params_by_id = json.load(f)

keys_by_block = []

for v, event in params_by_id.items():
	event = type("Event", (object,), event)
	if event.event_id != 'Migrated':
		continue
	top = event.params[0]["value"]
	child = event.params[1]["value"]
	print(f"Block {event.block_num} migrated {top} Top and {child} Child keys")
	keys_by_block.append((event.block_num, top, child))

x = [d[0] for d in keys_by_block]
y1 = [d[1] for d in keys_by_block]
y2 = [d[2] for d in keys_by_block]

plt.title(f"Polkadot Storage Items migrated per block (total={sum(y1) + sum(y2):,})")
plt.xlabel("Block number")
plt.ylabel(f"# migrated keys (max={max(y1)})")
plt.plot(x, y1, label="Top keys")
plt.plot(x, y2, label="Child keys")
plt.legend()
plt.show()
