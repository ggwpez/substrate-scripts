"""
Script to replace all Polkadot-SDK crates with a local folder path.

It removes the `version =` and puts a `path =` in their place for all SDK dependencies.

Usage:

```
python diener.py --sdk <path-to-polkadot-sdk> --runtimes <path-to-runtimes>
```
"""

import argparse
import os
import toml
import shutil

from cargo_workspace import Workspace, DependencyLocation

def main(sdk_path: str, sdk_git: str, sdk_branch: str, runtimes_path: str):
	runtimes = Workspace.from_path(runtimes_path)
	sdk = Workspace.from_path(sdk_path)
	
	# We will use this to modify the Cargo.toml, since the cargo_workspace lib does not support modifications
	raw_runtimes = toml.load(open(os.path.join(runtimes_path, "Cargo.toml")))
	runtime_deps = raw_runtimes["workspace"]["dependencies"]

	raw_sdk = toml.load(open(os.path.join(sdk_path, "Cargo.toml")))

	for dep in runtimes.dependencies:
		renamed = dep.package or dep.name
		crate = sdk.crates.find_by_name(renamed)
		if crate is None:
			print(f"Runtime {renamed} not found in SDK")
			continue

		# Modify the Cargo.toml
		if dep.name not in runtime_deps:
			raise Exception(f"Bug: {dep.name} not found in runtime dependencies")

		runtime_deps[dep.name]["git"] = sdk_git
		runtime_deps[dep.name]["branch"] = sdk_branch
		runtime_deps[dep.name]["path"] = None
		runtime_deps[dep.name]["version"] = "*"

	# Backup original Cargo.toml
	shutil.copy(os.path.join(runtimes_path, "Cargo.toml"), os.path.join(runtimes_path, "Cargo.toml.bak"))
	# Write the modified Cargo.toml
	with open(os.path.join(runtimes_path, "Cargo.toml"), "w") as f:
		# Write command that we used to generate the Cargo.toml
		f.write(f"# AUTO-GENERATED FILE. DO NOT EDIT.\n")
		f.write(f"# Check backup Cargo.toml.bak for the original file.\n")
		f.write(f"# Script at https://github.com/ggwpez/substrate-scripts/blob/master/diener-git.py \n")
		f.write(f"# > python3 diener-git.py --sdk {sdk_path} --sdk-git {sdk_git} --sdk-branch {sdk_branch} --runtimes {runtimes_path}\n\n\n")
		toml.dump(raw_runtimes, f)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--sdk", type=str, required=True)
	parser.add_argument("--sdk-git", type=str, required=True)
	parser.add_argument("--sdk-branch", type=str, required=True)
	parser.add_argument("--runtimes", type=str, required=True)
	args = parser.parse_args()

	print(f"SDK: {args.sdk}")
	print(f"SDK Git: {args.sdk_git}")
	print(f"SDK branch: {args.sdk_branch}")
	print(f"Runtimes: {args.runtimes}")
	main(args.sdk, args.sdk_git, args.sdk_branch, args.runtimes)
