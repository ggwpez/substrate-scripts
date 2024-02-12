import json
import sys

input=sys.argv[1]

with open(input) as f:
	data = json.load(f)

diffs = data['system']['account']
delta_free = 0
delta_reserved = 0

for acc, diff in diffs.items():
	print(diff)
	if type(diff) is list:
		data = diff[1]['data']
		new_free = int(data['free'].replace(',', ''))
		new_reserved = int(data['reserved'].replace(',', ''))
		delta_free += new_free
		delta_reserved += new_reserved
		continue
	data = diff['data']
	
	old_free = int(data['free'][0].replace(',', ''))
	new_free = int(data['free'][1].replace(',', ''))
	delta = new_free - old_free
	delta_free += delta

	if 'reserved' in data:
		old_reserved = int(data['reserved'][0].replace(',', ''))
		new_reserved = int(data['reserved'][1].replace(',', ''))
		delta = new_reserved - old_reserved
		delta_reserved += delta

	print(f"{acc}: {old_free} -> {new_free} ~ {delta_free},{delta_reserved}")

delta = delta_free + delta_reserved
print(f"Total: {delta}")
