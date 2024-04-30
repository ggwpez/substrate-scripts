'''
Update the hashlocks of a cargo `vendor` directory.

This is useful when modifying the code in a `vendor` dir, since cargo will otherwise refuse to build.

Usage:
	python rehash.py [--path /path/to/workspace]
'''

import os
import sys
import json
import argparse
from hashlib import sha256

parser = argparse.ArgumentParser(description='Rehash all files in vendor directories')
parser.add_argument('--path', type=str, default=os.getcwd(), help='Cargo Workspace with a vendor dir in it')
args = parser.parse_args()

vendor = os.path.join(args.path, 'vendor')

if not os.path.exists(vendor):
	raise Exception(f'Vendor directory not found at: {vendor}')

def hash_file(file):
	with open(file, 'rb') as f:
		return sha256(f.read()).hexdigest()

def update_locks(dir, locks):
	for lock in locks:
		path = os.path.join(dir, lock)
		locks[lock] = hash_file(path)

dirs = os.listdir(vendor)
print(f'Updating hashlocks for {len(dirs)} vendor directories')

for d in dirs:
	path = os.path.join(vendor, d)
	
	hashlock_path = os.path.join(path, '.cargo-checksum.json')
	with open(hashlock_path, 'r') as f:
		hashlock = json.load(f)
	
	update_locks(path, hashlock['files'])

	with open(hashlock_path, 'w') as f:
		json.dump(hashlock, f, indent=2)
