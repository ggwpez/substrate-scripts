"""
Tries to find broken internal rust dependencies and fixes then.
"""

import os
import sys
import toml
import re

DIR = sys.argv[1]
print("🔎 Checking folder %s" % DIR)

# Some regex replace rules to find the correct git path in case it is not a local dep.
# This is quite hacky, but `cargo build` should ensure that we dont mess up.
replace_rules = [
	[[
		".*polkadot.*",
		"(pallet-)?xcm",
		"polkadot-primitives-test-helpers",
	], "https://github.com/paritytech/polkadot.git"],
	[[
		".*cumulus.*",
	  	".*bridge-hub.*",
	  	"parachain-info",
	  	"^bp-\\w+",
	  	"^(pallet-)?bridge-\\w+",
		"parachains-runtimes-test-utils",
	], "https://github.com/paritytech/cumulus.git"],
]

# Maps crate name to [manifest, path].
crates = {}

for root, dirs, files in os.walk(DIR):
	if "target" in root:
		continue
	for file in files:
		if file == "Cargo.toml":
			path = os.path.join(root, file)
			with open(path, "r") as f:
				content = f.read()
				manifest = toml.loads(content)
				if 'workspace' in manifest:
					continue
				name = manifest['package']['name']
				crates[name] = [manifest, path]

print("📦 Found %d crates" % len(crates))

# Now check that all the deps are correct.
for name in crates:
	[manifest, path] = crates[name]
	print("📜 Checking crate %s" % name)
	for dep_name in manifest['dependencies']:
		# Account for renames.
		dep = manifest['dependencies'][dep_name]

		if 'package' in dep:
			dep_name = dep['package']
		if 'path' in dep:
			dep_path = dep['path']
		else:
			continue
		if not dep_name in crates:
			found = False
			# Correct the path if it is a git repo.
			for [rules, gh] in replace_rules:
				if found:
					break
				for rule in rules:
					if re.match(rule, dep_name):
						print("🔗 Patching GH dep %s -> %s" % (dep_name, gh))
						dep['git'] = gh
						dep.pop('path')
						dep['branch'] = 'master'
						found = True
						break
			if not found:
				print("💥 Could not correct GH dep %s -> %s" % (name, dep_name))
				sys.exit(1)
		else:
			# check that the relative path is correct.
			[dep_manifest, dep_path] = crates[dep_name]
			dep_path = os.path.dirname(dep_path)
			rel_path = os.path.relpath(dep_path, os.path.dirname(path))
			if rel_path != dep['path']:
				print("🔗 Patching relative dep %s -> %s" % (dep_name, rel_path))
				dep['path'] = rel_path
			else:
				print("✅ Correct dep %s -> %s" % (dep_name, rel_path))
	
	# Write back the manifest.
	with open(path, "w") as f:
		f.write(toml.dumps(manifest))
		print("✅ Fixed crate %s" % name)
