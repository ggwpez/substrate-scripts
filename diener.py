"""
Script to replace all Polkadot-SDK crates with a local folder path.

It removes the `version =` and puts a `path =` in their place for all SDK dependencies.

Usage:

```
python3 diener.py --sdk <path-to-polkadot-sdk> --runtimes <path-to-runtimes>
```

Deps:

- pip install toml cargo-workspace
"""

import argparse
import os
import toml
import shutil
from cargo_workspace import Workspace, DependencyLocation

def main(sdk_path: str, runtimes_path: str):
	runtimes = Workspace.from_path(runtimes_path)
	sdk = Workspace.from_path(sdk_path)
	
	# We will use this to modify the Cargo.toml, since the cargo_workspace lib does not support modifications
	raw_runtimes = toml.load(open(os.path.join(runtimes_path, "Cargo.toml")))
	runtime_deps = raw_runtimes["workspace"]["dependencies"]

	raw_sdk = toml.load(open(os.path.join(sdk_path, "Cargo.toml")))
	sdk_crates = raw_sdk["workspace"]["dependencies"]

	# Remove all the versions from the SDK crates
	for crate in sdk_crates:
		if "path" in sdk_crates[crate]:
			sdk_crates[crate]["version"] = None

	for dep in runtimes.dependencies:
		renamed = dep.package or dep.name
		crate = sdk.crates.find_by_name(renamed)
		if crate is None:
			print(f"Runtime {renamed} not found in SDK")
			continue
		# Check that if the name exists in both, do nothing
		if runtimes.crates.find_by_name(renamed) is not None:
			print(f"Name clash: {dep.name} in runtime and SDK. Ignoring")
			continue

		# Remove the Cargo.toml from the path
		path = os.path.relpath(crate.abs_path, runtimes_path)
		path = path.replace("/Cargo.toml", "")
		print(f"Patching dependency {renamed} to {path}")

		# Modify the Cargo.toml
		if dep.name not in runtime_deps:
			raise Exception(f"Bug: {dep.name} not found in runtime dependencies")

		runtime_deps[dep.name]["path"] = path
		runtime_deps[dep.name]["version"] = None
		runtime_deps[dep.name]["git"] = None
		runtime_deps[dep.name]["branch"] = None

		# Modify the Cargo.toml of the SDK crate and set the expected version
		crate_toml = toml.load(open(crate.abs_path))
		crate_toml["package"]["version"] = dep.version
		with open(crate.abs_path, "w") as f:
			toml.dump(crate_toml, f)

	# Backup original Cargo.toml
	shutil.copy(os.path.join(runtimes_path, "Cargo.toml"), os.path.join(runtimes_path, "Cargo.toml.bak"))

	# Write the modified Cargo.toml
	with open(os.path.join(runtimes_path, "Cargo.toml"), "w") as f:
		toml.dump(raw_runtimes, f)

	# Write the modified Cargo.toml of the SDK
	with open(os.path.join(sdk_path, "Cargo.toml"), "w") as f:
		toml.dump(raw_sdk, f)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--sdk", type=str, required=True)
	parser.add_argument("--runtimes", type=str, required=True)
	args = parser.parse_args()

	print(f"SDK: {args.sdk}")
	print(f"Runtimes: {args.runtimes}")
	main(args.sdk, args.runtimes)
