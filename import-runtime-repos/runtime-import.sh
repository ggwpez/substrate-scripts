#!/usr/bin/env bash
set -eo pipefail

# This script reproduces <https://github.com/polkadot-fellows/runtimes/pull/28>
# Please run the script in this directory.

# Requirements:
# - Stable Rust version
# - python3
# - sha256sum
# - git

# Opts for commit signing:
export SIGN_ARGS="--signoff --no-gpg-sign"

# check folder name:
if [[ ! $(basename "$PWD") == "import-runtime-repos" ]]; then
	echo "Please run this script from the import-runtime-repos folder."
	exit 1
fi

# Clone if not exists
if [[ ! -d "polkadot-sdk" ]]; then
	echo "Cloning polkadot-sdk"
	git clone https://github.com/paritytech/polkadot-sdk --branch v1.1.0-rc2 --depth 1 polkadot-sdk -q
else
	cd polkadot-sdk
	git checkout v1.1.0-rc2 -q
	cd ..
fi

# Clone if not exists
if [[ ! -d "runtimes" ]]; then
	echo "Cloning runtimes"
	git clone https://github.com/polkadot-fellows/runtimes --branch main -q
else
	cd runtimes
	git checkout main -q
	cd ..
fi

./copy-runtime-files.sh polkadot-sdk runtimes
