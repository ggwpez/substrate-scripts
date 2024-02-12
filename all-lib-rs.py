# Parse a file that has some lines in the form of:
# ... external crate `$DEPENDENCY` unused in `$CRATE` ...

import re
import sys
import json
import os
import toml

file_path = sys.argv[1]
root_dir = sys.argv[2]

with open(file_path, "r") as f:
	lines = f.readlines()

# Maps a crate to all its unused dependencies
to_remove = {}

for line in lines:
	if "unused in" in line:
		m = re.match(r".*`(.*)` unused in `(.*)`.*", line)
		if m:
			dep = m.group(1).replace("_", "-")
			crate = m.group(2).replace("_", "-")
			#print(f"{dep} is unused in {crate}")
			if not crate in to_remove:
				to_remove[crate] = []
			to_remove[crate].append(dep)

# Go through all Cargo.toml files recursively and remove the unused dependencies
for root, dirs, files in os.walk(root_dir):
	# skip the target folder
	if "target" in root:
		continue

	for file in files:
		if file == "Cargo.toml":
			path = os.path.join(root, file)
			with open(path, "r") as f:
				data = toml.load(f)
			
			if "package" in data and "name" in data["package"]:
				crate = data["package"]["name"]
				if crate in to_remove:
					to_remove_deps = to_remove[crate]
					print(f"Removing {to_remove_deps} from {crate}")
