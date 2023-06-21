#!/usr/bin/env bash

# Script to import the runtimes into the fellowship runtimes repo.
# Run this with the monorepo as argument and find the result in `polkadot-sdk.filtered`.

set -e

# First arg is the CWD.
CWD=$1
# wtf...
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $CWD
echo "Working in $CWD"

SIGN_ARGS="--signoff --no-gpg-sign"

mkdir -p relay/runtimes
git mv polkadot/runtime/common/ relay/common
git mv polkadot/runtime/kusama/ relay/runtimes/kusama
git mv polkadot/runtime/metrics/ relay/runtimes/metrics
git mv polkadot/runtime/parachains/ relay/runtimes/parachains
git mv polkadot/runtime/polkadot/ relay/runtimes/polkadot

git rm -rf polkadot
git add --all
git commit -m "Move relay runtimes" $SIGN_ARGS

mkdir -p system-parachains/runtimes/asset-hubs
mkdir -p system-parachains/runtimes/bridge-hubs
mkdir -p system-parachains/runtimes/collectives

git mv cumulus/parachains/runtimes/assets/common system-parachains/runtimes/asset-hubs/common
git mv cumulus/parachains/runtimes/assets/test-utils system-parachains/runtimes/asset-hubs/common/test-utils
git mv cumulus/parachains/runtimes/assets/asset-hub-polkadot system-parachains/runtimes/asset-hubs/asset-hub-polkadot
git mv cumulus/parachains/runtimes/assets/asset-hub-kusama system-parachains/runtimes/asset-hubs/asset-hub-kusama

git mv cumulus/parachains/runtimes/bridge-hubs/bridge-hub-kusama system-parachains/runtimes/bridge-hubs/bridge-hub-kusama
git mv cumulus/parachains/runtimes/bridge-hubs/bridge-hub-polkadot system-parachains/runtimes/bridge-hubs/bridge-hub-polkadot
git mv cumulus/parachains/runtimes/bridge-hubs/bridge-hub-rococo system-parachains/runtimes/bridge-hubs/bridge-hub-rococo

git mv cumulus/parachains/runtimes/collectives/collectives-polkadot system-parachains/runtimes/collectives/collectives-polkadot

git mv cumulus/parachains/common/ system-parachains/common
mkdir -p system-parachains/common/pallets/
git mv cumulus/pallets/collator-selection/ system-parachains/common/pallets/collator-selection

rm -rf cumulus
git add --all
git commit -m "Move parachain runtimes" $SIGN_ARGS

#python3 $SCRIPT_DIR/filter-folder.py relay system-parachains rustfmt.toml
