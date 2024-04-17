# Creates a polkadot-sdk crate that re-exports all other crates.

import argparse
import os
import re
import toml
import shutil

from cargo_workspace import Workspace

exclude = ["rococo-runtime"]

def delete_umbrella(path):
	umbrella_dir = os.path.join(path, "umbrella")
	if os.path.exists(umbrella_dir):
		print(f"Deleting {umbrella_dir}")
		shutil.rmtree(umbrella_dir)
	# remove the umbrella crate from the workspace
	manifest = os.path.join(path, "Cargo.toml")
	manifest = open(manifest, "r").read()
	manifest = re.sub(r'\s+"umbrella",\n', "", manifest)
	with open(os.path.join(path, "Cargo.toml"), "w") as f:
		f.write(manifest)

def add_to_workspace(path):
	manifest = os.path.join(path, "Cargo.toml")
	manifest = open(manifest, "r").read()
	manifest = re.sub(r'members = \[', 'members = [\n    "umbrella",\n', manifest)
	with open(os.path.join(path, "Cargo.toml"), "w") as f:
		f.write(manifest)
	
	os.chdir(path) # hack
	os.system(f"zepter") # enable the features
	# Taplo refuses to format the umbrella manifest, so we first run Zepter and then Taplo:
	#os.system(f"zepter f f -f --manifest-path .")
	#os.system(f"taplo format --config .config/taplo.toml")

def main(path, version):
	delete_umbrella(path)
	workspace = Workspace.from_path(path)
	print(f'Indexed {workspace}')

	std_crates = [] # name -> path. use list for sorting
	nostd_crates = []
	for crate in workspace.crates:
		if crate.name == 'polkadot-sdk':
			continue
		if not crate.publish:
			print(f"Skipping {crate.name} as it is not published")
			continue

		# Check if the crate has a 'src/lib.rs':
		lib_path = os.path.dirname(crate.abs_path)
		lib_path = os.path.join(lib_path, "src", "lib.rs")
		
		if not os.path.exists(lib_path):
			print(f"Skipping {crate.name} as it does not have a 'src/lib.rs'")
			continue
		if crate.name in exclude:
			print(f"Skipping {crate.name} as it is in the exclude list")
			continue

		path = os.path.dirname(crate.rel_path)
		# check if the lib.rs has a `#![no_std]` attribute
		with open(lib_path, "r") as f:
			content = f.read()
			if "#![no_std]" in content or '#![cfg_attr(not(feature = "std"), no_std)]' in content:
				nostd_crates.append((crate.name, path))
			elif 'no_std' in content:
				raise Exception(f"Found 'no_std' in {lib_path} without knowing how to handle it")
			else:
				std_crates.append((crate.name, path))

	std_crates.sort()
	nostd_crates.sort()
	dependencies = {}

	for (crate, path) in nostd_crates:
		dependencies[crate] = {"path": f"../{path}", "default-features": False, "optional": True}
	
	for (crate, path) in std_crates:
		dependencies[crate] = {"path": f"../{path}", "default-features": False, "optional": True}
	
	features = {
		"default": [ "std" ],
		"std": [], # filled by Zepter
		"runtime": list([f"dep:{d}" for d, _ in nostd_crates]),
		"node": ["std"] + list([f"dep:{d}" for d, _ in std_crates]),
		"runtime-benchmarks": [], # filled by Zepter
		"try-runtime": [], # filled by Zepter
	}

	manifest = {
		"package": {
			"name": "polkadot-sdk",
			"version": version,
			"edition": "2021",
			"description": "Polkadot SDK umbrella crate",
		},
		"dependencies": dependencies,
		"features": features,
	}

	umbrella_dir = os.path.join(workspace.path, "umbrella")
	manifest_path = os.path.join(umbrella_dir, "Cargo.toml")
	lib_path = os.path.join(umbrella_dir, "src", "lib.rs")
	# create all dir
	os.makedirs(os.path.dirname(lib_path), exist_ok=True)
	# Write the manifest
	with open(manifest_path, "w") as f:
		toml_manifest = toml.dumps(manifest)
		f.write(toml_manifest)
		print(f"Wrote {manifest_path}")
	# and the lib.rs
	with open(lib_path, "w") as f:
		f.write(r'''#![cfg_attr(not(feature = "std"), no_std)]
		
#[cfg(feature = "runtime")]
pub use runtime::*;
#[cfg(feature = "node")]
pub use node::*;''')

		f.write('\n\n#[cfg(feature = "runtime")]\npub mod runtime {\n')
		for crate, _ in nostd_crates:
			use = crate.replace("-", "_")
			f.write(f"\tpub use {use};\n")
		f.write('}\n\n#[cfg(feature = "node")]\npub mod node {\n')
		for crate, _ in std_crates:
			use = crate.replace("-", "_")
			f.write(f"\tpub use {use};\n")
		f.write('}\n')
		print(f"Wrote {lib_path}")
	
	add_to_workspace(workspace.path)

def parse_args():
	parser = argparse.ArgumentParser(description="Create a polkadot-sdk crate")
	parser.add_argument("--sdk", type=str, default="polkadot-sdk", help="Path to the polkadot-sdk crate")
	parser.add_argument("--version", type=str, help="Version of the polkadot-sdk crate")
	return parser.parse_args()

if __name__ == "__main__":
	args = parse_args()
	main(args.sdk, args.version)
