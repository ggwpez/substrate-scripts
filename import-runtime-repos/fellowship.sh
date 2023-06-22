#!/usr/bin/env bash

# Script to import the runtimes into the fellowship runtimes repo.
# Run this on the monorepo output of the `monorepo.sh` script.

set -e

# First arg is the CWD.
CWD=$1
# wtf...
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $CWD
echo "Working in $CWD"

SIGN_ARGS="--signoff --no-gpg-sign"

# Re-write history again to move all folders to the correct place.
git filter-repo --force \
	--path-rename 'cumulus/pallets/collator-selection:system-parachains/common/pallets/collator-selection' \
	--path-rename 'cumulus/parachains/common:system-parachains/common' \
	--path-rename 'cumulus/parachains/runtimes/assets/asset-hub-kusama:system-parachains/runtimes/asset-hubs/asset-hub-kusama' \
	--path-rename 'cumulus/parachains/runtimes/assets/asset-hub-polkadot:system-parachains/runtimes/asset-hubs/asset-hub-polkadot' \
	--path-rename 'cumulus/parachains/runtimes/assets/common:system-parachains/runtimes/asset-hubs/common' \
	--path-rename 'cumulus/parachains/runtimes/assets/test-utils:system-parachains/runtimes/asset-hubs/common/test-utils' \
	--path-rename 'cumulus/parachains/runtimes/bridge-hubs/bridge-hub-kusama:system-parachains/runtimes/bridge-hubs/bridge-hub-kusama' \
	--path-rename 'cumulus/parachains/runtimes/bridge-hubs/bridge-hub-polkadot:system-parachains/runtimes/bridge-hubs/bridge-hub-polkadot' \
	--path-rename 'cumulus/parachains/runtimes/bridge-hubs/bridge-hub-rococo:system-parachains/runtimes/bridge-hubs/bridge-hub-rococo' \
	--path-rename 'cumulus/parachains/runtimes/collectives/collectives-polkadot:system-parachains/runtimes/collectives/collectives-polkadot' \
	--path-rename 'polkadot/runtime/common:relay/common' \
	--path-rename 'polkadot/runtime/kusama:relay/runtimes/kusama' \
	--path-rename 'polkadot/runtime/metrics:relay/runtimes/metrics' \
	--path-rename 'polkadot/runtime/parachains:relay/runtimes/parachains' \
	--path-rename 'polkadot/runtime/polkadot:relay/runtimes/polkadot'

# Re-write history to remove all commits that are in unrelated folders.
# NOTE we cannot use `git filter-repo` here, since it does not account for files that existed outside of the
# specified folders at one point in time.
python3 $SCRIPT_DIR/filter-folder.py \
	system-parachains/common/pallets/collator-selection \
	system-parachains/common \
	system-parachains/runtimes/asset-hubs/asset-hub-kusama \
	system-parachains/runtimes/asset-hubs/asset-hub-polkadot \
	system-parachains/runtimes/asset-hubs/common \
	system-parachains/runtimes/asset-hubs/common/test-utils \
	system-parachains/runtimes/bridge-hubs/bridge-hub-kusama \
	system-parachains/runtimes/bridge-hubs/bridge-hub-polkadot \
	system-parachains/runtimes/bridge-hubs/bridge-hub-rococo \
	system-parachains/runtimes/collectives/collectives-polkadot \
	relay/common \
	relay/runtimes/kusama \
	relay/runtimes/metrics \
	relay/runtimes/parachains \
	relay/runtimes/polkadot

# Hacky sed to fix all the dependencies that were internal, but are not anymore.
find . -type f -not -path target -not -path .git -exec sed -i 's|primitives = { package = "polkadot-primitives", path = ".*", default-features = false }|primitives = { git = "https://github.com/paritytech/substrate", default-features = false, branch = "master" }|g' {} \;
find . -type f -not -path target -not -path .git -exec sed -i 's|primitives = { package = "polkadot-primitives", path = ".*", default-features = false }|primitives = { git = "https://github.com/paritytech/substrate", default-features = false, branch = "master" }|g' {} \;
