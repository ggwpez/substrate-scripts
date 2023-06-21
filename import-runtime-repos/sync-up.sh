#!/usr/bin/env bash

set -e

# First arg is the CWD.
CWD=$1
# wtf...
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd $CWD
rm -rf cumulus2 cumulus2.filtered polkadot2 polkadot2.filtered runtimes-tmp

# Check if runtimes folder exists and otherwise clone
if [ ! -d "$CWD/runtimes-tmp" ]; then
	echo "Cloning runtimes repo..."
	git clone --quiet https://github.com/polkadot-fellows/runtimes --branch main runtimes-tmp > /dev/null
fi

cd $CWD/runtimes-tmp
rm -rf target
git fetch
git checkout main
git reset --hard origin/main
git branch -D oty-sync tmp-filter-cumulus tmp-filter-polkadot || true
git checkout -b oty-sync
echo "Reverting move files..."
git revert 82bd4e46aa2926c11d9e84d826a5ee0b6622b9bd 32a8bb16f2d47dca72121d5c433e974ff19f7bc0 62792169c182b24e9894a3f96278da948f19efbc --no-gpg-sign --no-edit > /dev/null
cd ..

COMMIT_DOT='b6b74fdf546c14bf9ac93c03916abda9ee33a52f'
echo "Cloning Polkadot..."
git clone --quiet https://github.com/paritytech/polkadot polkadot2 --branch master > /dev/null
cd polkadot2 && git reset --hard $COMMIT_DOT --quiet > /dev/null && cd ..

COMMIT_CUM='94122347676023c44fa43061ca870385f42e549a'
echo "Cloning Cumulus..."
git clone --quiet https://github.com/paritytech/cumulus cumulus2 --branch master > /dev/null
cd cumulus2 && git reset --hard $COMMIT_CUM --quiet > /dev/null && cd ..

cd polkadot2/
echo "Moving Polkadot to subfolder.."
git filter-repo --to-subdirectory-filter polkadot --quiet --force
echo "Filtering Polkadot files..."
python3 $SCRIPT_DIR/filter-folder.py polkadot/runtime --quiet

cd ../cumulus2/
echo "Moving Cumulus to subfolder.."
git filter-repo --to-subdirectory-filter cumulus --quiet --force
echo "Filtering Cumulus files..."
python3 $SCRIPT_DIR/filter-folder.py cumulus/parachains cumulus/pallets/collator-selection

cd $CWD/runtimes-tmp
echo "Importing Polkadot..."
git checkout --orphan tmp-filter-polkadot
git rm -rf .
git pull ../polkadot2.filtered/ master -q

echo "Importing Cumulus..."
git checkout oty-sync
git checkout --orphan tmp-filter-cumulus
git rm -rf .
git pull ../cumulus2.filtered/ master -q

echo "Merging Polkadot and Cumulus..."
git checkout oty-sync
# NOTE: We use -X theirs here since the only changes that there can be are in the Cargo.toml files
# and those will be fixed up later.
git merge -X theirs --allow-unrelated-histories tmp-filter-polkadot -m "Sync up Polkadot ${COMMIT_DOT:0:10}" -q --signoff --no-gpg-sign
mkdir -p relay/runtimes

git mv polkadot/runtime/common/ relay/common > /dev/null
git mv polkadot/runtime/kusama/ relay/runtimes/kusama > /dev/null
git mv polkadot/runtime/metrics/ relay/runtimes/metrics > /dev/null
git mv polkadot/runtime/parachains/ relay/runtimes/parachains > /dev/null
git mv polkadot/runtime/polkadot/ relay/runtimes/polkadot > /dev/null
#git mv polkadot/runtime/test-runtime/ relay/runtimes/test-runtime

git rm -rf polkadot
git add --all
git commit -m "Move Polkadot to root folder" --signoff --no-gpg-sign
#git commit --amend --signoff

git merge -X theirs --allow-unrelated-histories tmp-filter-cumulus -m "Sync up Cumulus ${COMMIT_CUM:0:10}" -q --signoff --no-gpg-sign
mkdir -p system-parachains/runtimes/asset-hubs
mkdir -p system-parachains/runtimes/bridge-hubs
mkdir -p system-parachains/runtimes/collectives

git mv cumulus/parachains/runtimes/assets/common system-parachains/runtimes/asset-hubs/common > /dev/null
git mv cumulus/parachains/runtimes/assets/test-utils system-parachains/runtimes/asset-hubs/common/test-utils > /dev/null
git mv cumulus/parachains/runtimes/assets/statemint system-parachains/runtimes/asset-hubs/asset-hub-polkadot > /dev/null
git mv cumulus/parachains/runtimes/assets/statemine system-parachains/runtimes/asset-hubs/asset-hub-kusama > /dev/null

git mv cumulus/parachains/runtimes/bridge-hubs/bridge-hub-kusama system-parachains/runtimes/bridge-hubs/bridge-hub-kusama > /dev/null
git mv cumulus/parachains/runtimes/bridge-hubs/bridge-hub-polkadot system-parachains/runtimes/bridge-hubs/bridge-hub-polkadot > /dev/null

git mv cumulus/parachains/runtimes/collectives/collectives-polkadot system-parachains/runtimes/collectives/collectives-polkadot > /dev/null

git mv cumulus/parachains/common/ system-parachains/common > /dev/null
mkdir -p system-parachains/common/pallets/
git mv cumulus/pallets/collator-selection/ system-parachains/common/pallets/collator-selection > /dev/null

rm -rf cumulus
git add --all
git commit -m "Move Cumulus to root folder" --signoff --no-gpg-sign
#git commit --amend --signoff
git cherry-pick 82bd4e46aa2926c11d9e84d826a5ee0b6622b9bd --no-gpg-sign

echo "Sanity checking history..."
# There should be x commits for cumulus
COMMITS=$(git log --no-merges -M --oneline --follow -- system-parachains/runtimes/asset-hubs/asset-hub-kusama/src/lib.rs | wc -l)
if [ "$COMMITS" -ne "134" ]; then
	echo "Expected 134 commits, got $COMMITS"
fi
# And y for polkadot
COMMITS=$(git log --no-merges --oneline -M --follow -- relay/runtimes/polkadot/src/lib.rs | wc -l)
if [ "$COMMITS" -ne "658" ]; then
	echo "Expected 658 commits, got $COMMITS"
fi

echo "Checking dependency resolves..."
python $SCRIPT_DIR/check-deps.py $CWD/runtimes-tmp
echo "Updating Substrate and Polkadot deps..."
cargo update -p sp-io --quiet
cargo update -p polkadot-primitives --quiet
git add Cargo.lock
git commit -m "Update Substrate and Polkadot deps" --signoff --no-gpg-sign
git cherry-pick 93af0b1cadf220286c18193b5bfc7c9a24d0555e --no-gpg-sign

echo "Cargo test..."
cargo test -q --all-features --all-targets

#tree -I 'target' -d || echo "Tree command not found - skipping"
echo "Imported Polkadot $COMMIT_DOT"
echo "Imported Cumulus  $COMMIT_CUM"
echo "All done"


356abc23a2cd67b80c68757ce8045e64734da4a6 4a21269f199c4359d283b1ce0469924a10d2ecbe
