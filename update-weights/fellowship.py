import os
import json
import subprocess
import sys

# First arg is the cwd
cwd = os.path.abspath(os.path.expanduser(os.path.expandvars(sys.argv[1])))
# Second arg is the polkadot node
polkadot = os.path.abspath(os.path.expanduser(os.path.expandvars(sys.argv[2])))
# Path of the script
script_path = os.path.dirname(os.path.realpath(__file__))

PROFILE="production"

runtime_folders = []
for root, dirs, files in os.walk(cwd):
	for file in files:
		if file == "Cargo.toml" and "target" not in root:
			with open(os.path.join(root, file), 'r') as f:
				if '-runtime"' in f.read():
					# Calculate the relative path to the runtime.
					rel = os.path.relpath(root, cwd)
					runtime_folders.append(rel)
					print("Found runtime: %s" % rel)
					break

for path in runtime_folders:
	print("Generating chain spec for %s" % path)
	# Call the polkadot node and generate the chain spec.
	binary = polkadot
	if "system-" in path:
		binary = binary + "-parachain"
	# The last path segment is the name of the runtime.
	runtime = path.split("/")[-1]
	spec = "spec-" + runtime + ".json"
	cmd = "%s build-spec --chain=%s-dev --disable-default-bootnode > %s" % (binary, runtime, spec)
	print("$ " + cmd)
	try:
		subprocess.check_call(cmd, shell=True)
	except subprocess.CalledProcessError as e:
		print("❌ Failed to generate spec for %s" % runtime)
		continue
	
	# Fixup spec file
	try:
		data = None
		with open(spec) as f:
			data = json.load(f)
			wasm_path = os.path.join(cwd, "target", PROFILE, "wbuild", runtime+"-runtime", runtime.replace('-', '_') + "_runtime.compact.compressed.wasm")
			print("Reading wasm from %s" % wasm_path)
			code = open(wasm_path, 'rb').read()
			data['genesis']['runtime']['system']['code'] = code.hex()
		with open(spec, 'w') as f:
			json.dump(data, f)
		
		print("✅ Patched %s" % spec)
	except Exception as e:
		print("❌ Failed to patch spec for %s" % runtime)
		continue

# Run the benchmarks:
for path in runtime_folders:
	if not "relay" in path: # TODO
		continue

	print("⚖️ Running benchmarks for %s" % path)
	binary = polkadot
	if "system-parachains" in path:
		binary = binary + "-parachain"
	runtime = path.split("/")[-1]
	spec = "spec-" + runtime + ".json"
	# First list all the benchmarks and parse the output.
	cmd = "%s benchmark pallet --chain=%s --list" % (binary, spec)
	print("$ " + cmd)
	try:
		output = subprocess.check_output(cmd, shell=True)
	except subprocess.CalledProcessError as e:
		print("❌ Failed to list benchmarks for %s" % path)
		continue
	pallets = []
	for line in output.decode("utf-8").split("\n"):
		# In the form of "pallet, extrinsic"
		if "," in line:
			pallet = line.split(",")[0]
			if pallet not in pallets and pallet != "pallet":
				pallets.append(pallet)
				print("Found pallet: %s" % pallet)
	
	# Now run the benchmarks for each pallet.
	for pallet in pallets:
		cmd = "%s benchmark pallet --steps=2 --repeat=1 --chain=%s --pallet=%s --extrinsic="" --output=%s --header=%s --steps=2 --repeat=1 --no-median-slopes --no-min-squares" % (binary, spec, pallet, os.path.join(cwd, path, "src", "weights"), os.path.join(script_path, "header.txt"))
		print("$ " + cmd)
		try:
			subprocess.check_call(cmd, shell=True)
		except subprocess.CalledProcessError as e:
			print("❌ Failed to run benchmarks for %s" % path)
			continue
		print("✅ Ran benchmarks for %s" % path)
