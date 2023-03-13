#!/usr/bin/env bash

set -e

# First arg is the CWD.
CWD=$1

cd $CWD

echo "Cloning Polkadot..."
git clone https://github.com/paritytech/polkadot polkadot2 --branch master --quiet
echo "Cloning Cumulus..."
git clone https://github.com/paritytech/cumulus cumulus2 --branch master --quiet

cd polkadot2/
COMMIT_DOT=$(git rev-parse HEAD)
echo "Moving Polkadot to subfolder.."
git filter-repo --to-subdirectory-filter polkadot --quiet
echo "Filtering Polkadot files..."
python3 filter-folder.py polkadot/runtime --quiet

cd ../cumulus2/
COMMIT_CUM=$(git rev-parse HEAD)
echo "Moving Cumulus to subfolder.."
git filter-repo --to-subdirectory-filter cumulus --quiet
echo "Filtering Cumulus files..."
python3 filter-folder.py cumulus/parachains

cd ../runtimes
git checkout main
git checkout -b tmp-init

echo "Importing Polkadot..."
git checkout --orphan tmp-filter-polkadot
git rm -f LICENSE
git pull ../polkadot2.filtered/ master -q

echo "Importing Cumulus..."
git checkout tmp-init
git checkout --orphan tmp-filter-cumulus
git rm -f LICENSE
git pull ../cumulus2.filtered/ master -q

echo "Merging Polkadot and Cumulus..."
git checkout tmp-init
git merge --allow-unrelated-histories tmp-filter-polkadot -m "Import Polkadot" --no-gpg-sign -q
mkdir -p relay/runtimes

git mv polkadot/runtime/common/ relay/common
git mv polkadot/runtime/kusama/ relay/runtimes/kusama
git mv polkadot/runtime/metrics/ relay/runtimes/metrics
git mv polkadot/runtime/parachains/ relay/runtimes/parachains
git mv polkadot/runtime/polkadot/ relay/runtimes/polkadot
git mv polkadot/runtime/test-runtime/ relay/runtimes/test-runtime

git rm -rf polkadot
git add --all
git commit -m "Move Polkadot to root folder" --no-gpg-sign

git merge --allow-unrelated-histories tmp-filter-cumulus -m "Import Cumulus" --no-gpg-sign -q
mkdir -p system-parachains/runtimes/asset-hubs
mkdir -p system-parachains/runtimes/bridge-hubs
mkdir -p system-parachains/runtimes/collectives

git mv cumulus/parachains/runtimes/assets/common system-parachains/runtimes/asset-hubs/common
git mv cumulus/parachains/runtimes/assets/statemint system-parachains/runtimes/asset-hubs/assets-hub-polkadot
git mv cumulus/parachains/runtimes/assets/statemine system-parachains/runtimes/asset-hubs/assets-hub-kusama

git mv cumulus/parachains/runtimes/bridge-hubs/bridge-hub-kusama system-parachains/runtimes/bridge-hubs/bridge-hub-kusama
git mv cumulus/parachains/runtimes/bridge-hubs/bridge-hub-polkadot system-parachains/runtimes/bridge-hubs/bridge-hub-polkadot

git mv cumulus/parachains/runtimes/collectives/collectives-polkadot system-parachains/runtimes/collectives/collectives-polkadot

git mv cumulus/parachains/integration-tests/ system-parachains/integration-tests
git mv cumulus/parachains/common/ system-parachains/common

rm -rf cumulus
git add --all
git commit -m "Move Cumulus to root folder" --no-gpg-sign

echo "Importing meta files..."
git cherry-pick 81488550bc0e1329eb2fe64b5ae4065693229107 --no-gpg-sign
echo "Creating workspace..."
git cherry-pick bd9089eb24c050aae74221d8c980879ecaed8991 --no-gpg-sign

echo "Moved Polkadot from commit $COMMIT_DOT"
echo "Moved Cumulus from commit $COMMIT_CUM"

echo "Checking dependency resolves..."
python check-deps.py
echo "Checking build..."
SKIP_WASM_BUILD=1 cargo check --all-features -q

tree -I 'target' -d || echo "Tree command not found - skipping"
echo "All done"
