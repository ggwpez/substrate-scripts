# Migration script for https://github.com/paritytech/substrate/pull/13475
# Apply to the root directory of your repo like:
#
#   python3 migrate-from-parts.py ../polkadot

import os
import sys

def process_split(input, dimension):
	open = 0
	for i in range(len(input)):
		if input[i] == "(":
			open += 1
		elif input[i] == ")":
			open -= 1
		if open == 0:
			value = input[1:i].strip()
			# remove the last comma
			if value[-1] == ",":
				value = value[:-1]
			if dimension == "ref_time":
				return "Weight::from_parts(" + value + ", 0)" + input[i+1:]
			elif dimension == "proof_size":
				return "Weight::from_parts(0, " + value + ")" + input[i+1:]
	return input

def process_content(input, dimension):
	split = input.split("Weight::from_" + dimension)
	output = ""
	for i, s in enumerate(split):
		if i == 0:
			output += s
		else:
			output += process_split(s, dimension)
	return output

dir = sys.argv[1]
print("Searching in directory: %s" % dir)

# Go through all the files in the current directory recursively besides the target directory.
for root, dirs, files in os.walk(dir):
	if "target" in root:
		continue
	for file in files:
		# If the file ends with .rs
		if file.endswith(".rs"):
			path = os.path.join(root, file)
			print("Processing file: %s" % path)
			# Open the file and write back the processed string
			with open(path, "r+") as f:
				content = f.read()
				content = process_content(content, "ref_time")
				content = process_content(content, "proof_size")
				# Write back
				f.seek(0)
				f.write(content)
				f.truncate()
