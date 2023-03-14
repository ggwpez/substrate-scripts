#!/usr/bin/env bash

set -e

# First arg is the CWD.
CWD=$1
# wtf...
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $CWD

echo "Cloning Polkadot..."
git clone https://github.com/paritytech/polkadot polkadot2 --branch master --quiet
cd polkadot2 && git reset --hard c02f9adb6e31357a21fb0d07005441db71ddc9d6 && cd ..
echo "Cloning Cumulus..."
git clone https://github.com/paritytech/cumulus cumulus2 --branch master --quiet
cd cumulus2 && git reset --hard 836f13e24c74fcc0fe70eeeffd88214c88bf2316 && cd ..

cd polkadot2/
COMMIT_DOT=$(git rev-parse HEAD)
echo "Moving Polkadot to subfolder.."
git filter-repo --to-subdirectory-filter polkadot --quiet --force
echo "Filtering Polkadot files..."
python3 $SCRIPT_DIR/filter-folder.py polkadot/runtime --quiet

cd ../cumulus2/
COMMIT_CUM=$(git rev-parse HEAD)
echo "Moving Cumulus to subfolder.."
git filter-repo --to-subdirectory-filter cumulus --quiet --force
echo "Filtering Cumulus files..."
python3 $SCRIPT_DIR/filter-folder.py cumulus/parachains

cd $CWD/runtimes
rm -rf target
git checkout main
git branch -D tmp-init tmp-filter-cumulus tmp-filter-polkadot || true
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
git merge --allow-unrelated-histories tmp-filter-polkadot -m "Import Polkadot" -q
mkdir -p relay/runtimes

git mv polkadot/runtime/common/ relay/common
git mv polkadot/runtime/kusama/ relay/runtimes/kusama
git mv polkadot/runtime/metrics/ relay/runtimes/metrics
git mv polkadot/runtime/parachains/ relay/runtimes/parachains
git mv polkadot/runtime/polkadot/ relay/runtimes/polkadot
git mv polkadot/runtime/test-runtime/ relay/runtimes/test-runtime

git rm -rf polkadot
git add --all
git commit -m "Move Polkadot to root folder"

git merge --allow-unrelated-histories tmp-filter-cumulus -m "Import Cumulus" -q
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
git commit -m "Move Cumulus to root folder"

echo "Importing meta files..."
git cherry-pick cfcaae413ed0678907b151e356add968fc9a4a3c
echo "Creating workspace..."
git cherry-pick 6611c8fb8b6f993bd15392cc99d6857c17231694

echo "Sanity checking history..."
# There should be 128 commits
COMMITS=$(git log --no-merges -M --oneline --follow -- system-parachains/runtimes/asset-hubs/assets-hub-kusama/src/lib.rs | wc -l)
if [ "$COMMITS" -ne "128" ]; then
	echo "Expected 128 commits, got $COMMITS"
	exit 1
fi
# And 648 for polkadot
COMMITS=$(git log --no-merges --oneline -M --follow -- relay/runtimes/polkadot/src/lib.rs | wc -l)
if [ "$COMMITS" -ne "648" ]; then
	echo "Expected 648 commits, got $COMMITS"
	exit 1
fi

echo "Checking dependency resolves..."
python $SCRIPT_DIR/check-deps.py $CWD/runtimes
echo "Checking build..."
SKIP_WASM_BUILD=1 cargo check --all-features -q

tree -I 'target' -d || echo "Tree command not found - skipping"
echo "Imported Polkadot $COMMIT_DOT"
echo "Imported Cumulus  $COMMIT_CUM"
echo "All done"
