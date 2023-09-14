#!/usr/bin/env bash

# Script to import the runtimes into the fellowship runtimes repo.
# Run this on the monorepo output of the `monorepo.sh` script.

set -eox pipefail

# First arg is the CWD.
CWD=$1
# wtf...
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SIGN_ARGS="--signoff --no-gpg-sign"

# Next args are COMMIT_SUB, COMMIT_DOT, COMMIT_CUM
COMMIT_SUB=$2
COMMIT_DOT=$3
COMMIT_CUM=$4
# Erro if any of these are empty.
if [ -z "$COMMIT_SUB" ] || [ -z "$COMMIT_DOT" ] || [ -z "$COMMIT_CUM" ]; then
	echo "Usage: ./fellowship.sh <CWD> <COMMIT_SUB> <COMMIT_DOT> <COMMIT_CUM>"
	exit 1
fi

cd $CWD
echo "Working in $CWD"
rm -rf polkadot-sdk

# Either unzip the polkadot.zip file or error.
if [ -f "polkadot-sdk.zip" ]; then
	unzip -q polkadot-sdk.zip
else
	echo "polkadot-sdk.zip not found. Run monorepo.sh first."
	exit 1
fi

cd polkadot-sdk
SIGN_ARGS="--signoff --no-gpg-sign"

echo "Fix all the dependencies that were internal, but are not anymore."
cargo r --manifest-path $SCRIPT_DIR/fix-deps/Cargo.toml -- .
echo "Diener workspacify"
diener workspacify

git add --all && git commit -m "Diener workspacify" $SIGN_ARGS

echo '
[workspace.package]
authors = ["Parity Technologies <admin@parity.io>"]
edition = "2021"
repository = "https://github.com/paritytech/polkadot.git"
license = "GPL-3.0-only"
version = "1.0.0"' >> Cargo.toml

git add --all && git commit -m "Add package metadata to workspace" $SIGN_ARGS

echo "Fix dependnecy revs"
# We cannot just let the dependencies point to "master", that would get out-dated.
cargo update -p polkadot-primitives --precise $COMMIT_DOT
cargo update -p sp-io --precise $COMMIT_SUB
# NOTE: Assumes to be run against Cumulus master - therefore no patching for that.

git add --all && git commit -m "Fix dependency revs" $SIGN_ARGS

echo "Checking dependency resolves..."
python3 $SCRIPT_DIR/check-deps.py $PWD

echo "Running cargo check... (You can CTRL+C now)"
SKIP_WASM_BUILD=1 cargo test "*-runtime" -q # Build all but only execute 'runtime' tests.
