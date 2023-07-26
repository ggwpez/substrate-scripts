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

# Either unzip the polkadot.zip file or error.
if [ -f "polkadot-sdk.zip" ]; then
	unzip -q polkadot-sdk.zip
else
	echo "polkadot-sdk.zip not found. Run monorepo.sh first."
	exit 1
fi

cd polkadot-sdk
SIGN_ARGS="--signoff --no-gpg-sign"

# Re-write history again to move all folders to the correct place.
git filter-repo --force \
	--path-rename 'cumulus/Cargo.lock:Cargo.lock' \
	--path-rename 'cumulus/parachains/runtimes/assets/asset-hub-kusama:system-parachains/asset-hubs/asset-hub-kusama' \
	--path-rename 'cumulus/parachains/runtimes/assets/asset-hub-polkadot:system-parachains/asset-hubs/asset-hub-polkadot' \
	--path-rename 'cumulus/parachains/runtimes/bridge-hubs/bridge-hub-kusama:system-parachains/bridge-hubs/bridge-hub-kusama' \
	--path-rename 'cumulus/parachains/runtimes/bridge-hubs/bridge-hub-polkadot:system-parachains/bridge-hubs/bridge-hub-polkadot' \
	--path-rename 'cumulus/parachains/runtimes/bridge-hubs/bridge-hub-rococo:system-parachains/bridge-hubs/bridge-hub-rococo' \
	--path-rename 'cumulus/parachains/runtimes/collectives/collectives-polkadot:system-parachains/collectives/collectives-polkadot' \
	--path-rename 'polkadot/runtime/kusama:relay/kusama' \
	--path-rename 'polkadot/runtime/polkadot:relay/polkadot'

#	--path-rename 'polkadot/runtime/metrics:relay/runtimes/metrics' \
#	--path-rename 'cumulus/parachains/common:system-parachains/common' \
#	--path-rename 'cumulus/parachains/runtimes/assets/common:system-parachains/runtimes/asset-hubs/common' \
#	--path-rename 'polkadot/runtime/parachains:relay/runtimes/parachains' \
#	--path-rename 'cumulus/pallets/collator-selection:system-parachains/common/pallets/collator-selection' \
#	--path-rename 'polkadot/runtime/common:relay/common' \
#	--path-rename 'cumulus/parachains/runtimes/assets/test-utils:system-parachains/runtimes/asset-hubs/common/test-utils' \

# Re-write history to remove all commits that are in unrelated folders.
# NOTE we cannot use `git filter-repo` here, since it does not account for files that existed outside of the
# specified folders at one point in time.
python3 $SCRIPT_DIR/filter-folder.py \
	Cargo.lock \
	system-parachains/asset-hubs/asset-hub-kusama \
	system-parachains/asset-hubs/asset-hub-polkadot \
	system-parachains/bridge-hubs/bridge-hub-kusama \
	system-parachains/bridge-hubs/bridge-hub-polkadot \
	system-parachains/bridge-hubs/bridge-hub-rococo \
	system-parachains/collectives/collectives-polkadot \
	relay/kusama \
	relay/polkadot

#relay/runtimes/metrics \
#system-parachains/common \
#system-parachains/runtimes/asset-hubs/common \
#relay/runtimes/parachains \
#system-parachains/common/pallets/collator-selection \
#relay/common \
#system-parachains/runtimes/asset-hubs/common/test-utils \

cd ../polkadot-sdk.filtered

# Remove old Polkadot, Substrate and Cumulus repos.
rm -rf polkadot substrate cumulus
git add --all && git commit -m "Remove trash" $SIGN_ARGS

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
