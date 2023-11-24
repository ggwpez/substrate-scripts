# Ensures that workspace dependencies are resolved via `path` and not something else.

import os
import sys
import toml

DIR = sys.argv[1]
print("🔎 Checking folder %s" % DIR)

crates = []
manifests = []
in_workspace = []
manifest_paths = []

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
					print("📜 Found workspace manifest")
					for member in manifest['workspace']['members']:
						in_workspace.append(member)
					continue
				manifests.append(manifest)
				# Cut off the root path and the trailing /Cargo.toml.
				path = path[len(DIR)+1:-11]
				manifest_paths.append(path)

if len(in_workspace) != len(manifest_paths):
	print("💥 Workspace members don't match manifest paths: %d vs %d" % (len(in_workspace), len(manifest_paths)))
	missing = []
	# Find out which ones are missing.
	for i, path in enumerate(manifest_paths):
		if not path in in_workspace:
			missing.append([path, manifests[i]])
	missing.sort()
	for path, manifest in missing:
		print("❌ %s in %s" % (manifest['package']['name'], path))
	sys.exit(1)

for manifest in manifests:
	name = manifest['package']['name']
	crates.append(name)

links = []
broken = []
# Now check that all the deps are correct.
for manifest in manifests:
	name = manifest['package']['name']

	def check_deps(deps):
		for dep in deps:
			# Account for renames.
			dep_name = dep
			if 'package' in deps[dep]:
				dep_name = deps[dep]['package']
			if dep_name in crates:
				links.append((name, dep_name))

				if not 'path' in deps[dep]:
					broken.append((name, dep_name))
	
	if 'dependencies' in manifest:
		check_deps(manifest['dependencies'])
	if 'dev-dependencies' in manifest:
		check_deps(manifest['dev-dependencies'])
	if 'build-dependencies' in manifest:
		check_deps(manifest['build-dependencies'])

crates.sort()
links.sort()
broken.sort()

print("📜 Found %d crates in the workspace" % len(crates))

for link in broken:
	print("❌ %s -> %s" % link)

if len(broken) > 0:
	print("💥 %d out of %d links are broken" % (len(broken), len(links)))
	sys.exit(1)
else:
	print("✅ All %d dependency links are correct" % len(links))
