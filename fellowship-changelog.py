# Generate a CHANGELOG entry when updating the Polkadot runtimes to a new SDK release.
# Please specify a new file as `--output` since it will be overwritten.
#
# example:
# 	python3 fellowship-changelog.py \
# 		--root ../polkadot-sdk/prdoc \
# 		--output ../runtimes/new_CHANGELOG.md \
# 		--versions 1.8.0,1.9.0,1.10.0,1.11.0,1.12.0,1.13.0 \
#		--audiences "Runtime User,Runtime Dev" \
#		--integration-mr-number 322

import argparse
import glob
import yaml
import sys
import re
import os

parser = argparse.ArgumentParser(description='Generate a changelog from PrDoc YAML files')
parser.add_argument('--root', help='The root directory to search for PrDoc YAML files in')
parser.add_argument('--output', help='The output file to write the changelog to')
parser.add_argument('--audiences', help='The audiences to include in the changelog')
parser.add_argument('--versions', help='The versions to include in the changelog')
parser.add_argument('--integration-mr-number', help='The integration merge request number')
args = parser.parse_args()

output_path = args.output
relevant_audiences = args.audiences.split(',')
versions = args.versions.split(',')
mr_number = args.integration_mr_number
root = args.root
# Version -> changes
output = []

for version in versions:
	path = f'{root}/{version}'
	if not os.path.exists(f'{path}'):
		print(f'Error: {path} does not exist')
		sys.exit(1)
	
	for file in glob.glob(f'{path}/*.prdoc'):
		file = open(file, 'r')
		prdoc = yaml.safe_load(file)
		title = prdoc["title"]
		number = os.path.basename(file.name).split('_')[1].split('-')[0].split('.')[0]
		relevant = False

		for doc in prdoc["doc"]:
			audiences = doc["audience"]

			if audiences in relevant_audiences or set(audiences).intersection(relevant_audiences):
				relevant = True
				break

		if relevant:
			print(f'👀 [{number}] {title}')
		else:
			print(f'🥱 [{number}] {title}')
			continue
		
		if 'westend' in title.lower() or 'rococo' in title.lower():
			continue

		short_version = version.split('.0')[0]
		title = title.rstrip('.').strip()
		# Replace `[Something]` with `Something:`
		title = re.sub(r'\[(.*?)\]', r'\1:', title)
		# Words that contain `::` should be put in backticks
		title = re.sub(r'(\w+::\w+)', r'`\1`', title)
		# Replace pallet_ with pallet- while ignoring the case
		title = re.sub(r'pallet_(\w+)', r'pallet-\1', title, flags=re.IGNORECASE)
		title = title[0].upper() + title[1:]
		line = f'- [[#{mr_number}](https://github.com/polkadot-fellows/runtimes/pull/{mr_number})] {title} ([SDK v{short_version} #{number}](https://github.com/paritytech/polkadot-sdk/pull/{number})).'
		output.append(line)

if len(output) == 0:
	print('No changes found')
	sys.exit(0)

categories = {
	'Added': [], 'Changed': [], 'Fixed': [], 'Removed': []
}
# Do some best-effort sorting
for line in output:
	if 'fix' in line.lower():
		categories['Fixed'].append(line)
	elif 'add' in line.lower() or 'introduce' in line.lower():
		categories['Added'].append(line)
	elif 'remove' in line.lower() or 'deprecate' in line.lower():
		categories['Removed'].append(line)
	else:
		categories['Changed'].append(line)

for cat in categories:
	# Ignore non-alphanum chars when sorting:
	categories[cat] = sorted(categories[cat], key=lambda x: re.sub(r'\W+', '', x.lower()))

file = open(output_path, 'w')
# Print the full invocation command as comment
file.write(f'<!--\n')
file.write(f'\tGenerated with https://github.com/ggwpez/substrate-scripts/blob/3b74931cbcfc083544713422828eae7e2c1c378b/fellowship-changelog.py\n\n')
file.write(f'\t{" ".join(sys.argv)}\n')
file.write(f'-->\n\n')

for category in ['Added', 'Changed', 'Fixed', 'Removed']:
	if len(categories[category]) > 0:
		file.write(f'### {category}\n\n')
		for line in categories[category]:
			file.write(f'{line}\n')
		file.write('\n')
