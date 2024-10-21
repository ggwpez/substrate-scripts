# Patch the runtime of a chainspec.
#
# Usage
#   python runtime-chainspec.py <chainspec.json> <code.wasm>

import json
import sys

def main():
	if len(sys.argv) != 3:
		print("Usage: python runtime-chainspec.py <input.json> <code.wasm>")
		sys.exit(1)

	with open(sys.argv[1], "r") as f:
		data = json.load(f)

	with open(sys.argv[2], "rb") as f:
		code = f.read()

	data["genesis"]["runtimeGenesis"]["code"] = "0x" + code.hex()

	with open(sys.argv[1], "w") as f:
		json.dump(data, f, indent=2)

if __name__ == "__main__":
	main()
