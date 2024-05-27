import os
import re
import sys
import json

from cargo_workspace import Workspace

ZEPTER_OUTPUT = '../zepter/renames.json'
ROOT = '../polkadot-sdk'
w = Workspace.from_path(ROOT)

def main():
	if os.path.exists(ZEPTER_OUTPUT):
		with open(ZEPTER_OUTPUT, 'r') as f:
			raw = f.read()[:-2]
			raw = f"[{raw}]"
			data = json.loads(raw)

	print(f"Processing {len(data)} alias conflicts")

	for conflict in data:
		name = conflict['name']
		# The crates that did not rename it.
		unrenamed = conflict['unnrenamed']
		# The name that it was renamed to and the crates that did it.
		renamed = conflict['renames']

		max_renamed = 0
		best_alias = None
		for a in renamed:
			if len(renamed[a]) > max_renamed:
				max_renamed = len(renamed[a])
				best_alias = a
	
		print(f"{name}: {len(unrenamed)} times unrenamed and {max_renamed} times renamed to {best_alias}")
		# First check if it should be renamed at all
		if len(unrenamed) > max_renamed:
			for a in renamed:
				for r in renamed[a]:
					unrename(name, a, r)
		else:
			for a in renamed:
				if a != best_alias:
					for r in renamed[a]:
						realias(name, a, best_alias, r)
			for crate in unrenamed:
				alias(name, best_alias, crate)

def unrename(name, alias, crate):
	print(f" -> unalias {name} as {alias} in {crate}")
	crate = w.crate_by_name(crate)

	# First fix the Cargo.toml
	with open(crate.abs_path, 'r') as f:
		lines = f.readlines()
	for i, line in enumerate(lines):
		if re.match(rf'^{alias} =', line):
			lines[i] = re.sub(rf'^{alias}', name, line)
			lines[i] = re.sub(rf'package = ".*?"\s*?,\s?', '', lines[i])			
	with open(crate.abs_path, 'w') as f:
		f.writelines(lines)

	fix_features(crate.abs_path, alias, name)
	print(f" -> fixed Cargo.toml in {name}")

def realias(name, old_alias, new_alias, crate):
	print(f" -> realias {name} from {old_alias} to {new_alias} in {crate}")

	# First fix the Cargo.toml
	crate = w.crate_by_name(crate)
	with open(crate.abs_path, 'r') as f:
		lines = f.readlines()
	for i, line in enumerate(lines):
		if re.match(rf'^{old_alias} =', line):
			lines[i] = re.sub(rf'^{old_alias}', new_alias, line)
	
	with open(crate.abs_path, 'w') as f:
		f.writelines(lines)
	fix_features(crate.abs_path, old_alias, new_alias)
	print(f" -> fixed Cargo.toml in {name}")
	return

def alias(name, alias, crate):
	print(f" -> alias {name} to {alias} in {crate}")

	# First fix the Cargo.toml
	crate = w.crate_by_name(crate)
	if crate is None:
		print(f" -> {crate} not found")
		return

	with open(crate.abs_path, 'r') as f:
		lines = f.readlines()
	for i, line in enumerate(lines):
		if re.match(rf'^{name} =', line):
			lines[i] = re.sub(rf'^{name}', alias, line)
			# insert the `package = "..."` into the beginning after the {
			if '{' in lines[i]:
				index = lines[i].find('{') + 1
				lines[i] = lines[i][:index] + f' package = "{name}",' + lines[i][index:]
			elif '=' in lines[i]:
				content = lines[i].split('=')[1].replace('"', '').strip()
				lines[i] = f'{alias} = {{ package = "{name}", version = "{content}" }}\n'
	with open(crate.abs_path, 'w') as f:
		f.writelines(lines)
	fix_features(crate.abs_path, name, alias)
	print(f" -> fixed Cargo.toml in {name}")
	return

def fix_features(path, old_name, new_name):
	with open(path, 'r') as f:
		lines = f.readlines()
	saw_features = False
	for i, line in enumerate(lines):
		if '[features]' in line:
			saw_features = True
		
		# Replace feature enables:
		lines[i] = lines[i].replace(f'"{old_name}/', f'"{new_name}/')
		print(f" -> {old_name}/ replacing with {new_name}/")
		# Replace dep feature enables:
		if saw_features:
			lines[i] = lines[i].replace(f'"{old_name}"', f'"{new_name}"')
		# Replace optional dep enables:
		lines[i] = lines[i].replace(f'"dep:{old_name}', f'"dep:{new_name}')
	with open(path, 'w') as f:
		f.writelines(lines)

if __name__ == "__main__":
	main()
