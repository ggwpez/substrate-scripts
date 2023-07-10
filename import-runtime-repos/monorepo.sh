#!/usr/bin/env bash

# Imports Substrate, Polkadot and Cumulus into a new filder. This changes all commit hashes and
# invalidates the signatures, since it re-writes history.

# Deps:
#  python3 -m pip install --user git-filter-repo
#  cargo install diener
# Run:
#  Create some work dir: mkdir ../../tmp
#  ./monorepo.sh ../../tmp

set -eo pipefail

# First arg is the CWD.
CWD=$1
# wtf...
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

SIGN_ARGS="--signoff --no-gpg-sign"
#SIGN_ARGS=""

# sha of cumulus/Cargo.lock file
#CUMULUS_SHA="7ab9d4f5baa87f8fee5a6e820a2ee8e4f0bdba44" # very old
#CUMULUS_SHA="21919c89ad99fc4e2e6f12dd6679eb2d41892ac3" # old
CUMULUS_SHA=$(curl -s "https://api.github.com/repos/paritytech/cumulus/commits?path=Cargo.lock&per_page=1" | jq -r '.[0].sha')

cd $CWD

echo "Removing old dirs..."
# NOTE we append `2` here in case some dingus runs it in his 'work' dir.
[ -d "cumulus2" ] && rm -rf cumulus2/
[ -d "polkadot2" ] && rm -rf polkadot2/
[ -d "substrate2" ] && rm -rf substrate2/

echo "Cloning Cumulus at ${CUMULUS_SHA}..."
# Either unzip the cumulus.zip file or clone the repo.
if [ -f "cumulus2.zip" ]; then
	unzip -q cumulus2.zip
else
	git clone https://github.com/paritytech/cumulus cumulus2 --quiet
	zip -r cumulus2.zip cumulus2
fi
cd cumulus2 && git reset --hard $CUMULUS_SHA

SUBSTRATE_SHA=$(cat Cargo.lock| grep 'substrate?' | uniq | sed 's/source = "git+https:\/\/github.com\/paritytech\/substrate?branch=master#//' | sed 's/"//')
POLKADOT_SHA=$(cat Cargo.lock| grep 'polkadot?' | uniq | sed 's/source = "git+https:\/\/github.com\/paritytech\/polkadot?branch=master#//' | sed 's/"//')
cd ..

echo "Cloning Polkadot at ${POLKADOT_SHA}..."
# Either unzip the polkadot.zip file or clone the repo.
if [ -f "polkadot2.zip" ]; then
	unzip -q polkadot2.zip
else
	git clone https://github.com/paritytech/polkadot polkadot2 --branch master --quiet
	zip -r polkadot2.zip polkadot2
fi
cd polkadot2 && git reset --hard $POLKADOT_SHA && cd ..

echo "Cloning Substrate at ${SUBSTRATE_SHA}..."
# Either unzip the substrate.zip file or clone the repo.
if [ -f "substrate2.zip" ]; then
	unzip -q substrate2.zip
else
	git clone https://github.com/paritytech/substrate substrate2 --branch master --quiet
	zip -r substrate2.zip substrate2
fi
cd substrate2 && git reset --hard $SUBSTRATE_SHA && cd ..

cd polkadot2/
COMMIT_DOT=$(git rev-parse HEAD)
echo "Moving Polkadot to subfolder.."
git filter-repo --to-subdirectory-filter polkadot --quiet --force

cd ../cumulus2/
COMMIT_CUM=$(git rev-parse HEAD)
echo "Moving Cumulus to subfolder.."
git filter-repo --to-subdirectory-filter cumulus --quiet --force

cd ../substrate2/
COMMIT_SUB=$(git rev-parse HEAD)
echo "Moving Substrate to subfolder.."
git filter-repo --to-subdirectory-filter substrate --quiet --force
# You can comment out the commands above if you have a copy already.
cd ..

mkdir -p polkadot-sdk
cd polkadot-sdk
git init -b master .
#git clone git@github.com:paritytech-stg/polkadot-sdk.git polkadot-sdk-new
#cd polkadot-sdk-new
touch .gitignore
git add .gitignore
git commit -m "Init" $SIGN_ARGS -q
echo "Creating tmp-init branch"
git checkout -b tmp-init

echo "Importing Polkadot..."
git checkout --orphan tmp-filter-polkadot
# Use polkadot2.filtered if you did the filtering above.
git pull ../polkadot2/ master -q

echo "Importing Cumulus..."
git checkout tmp-init
git checkout --orphan tmp-filter-cumulus
git pull ../cumulus2/ master -q

echo "Importing Substrate..."
git checkout tmp-init
git checkout --orphan tmp-filter-substrate
git pull ../substrate2/ master -q

echo "Merging Substrate, Polkadot and Cumulus..."
git checkout tmp-init
git merge --allow-unrelated-histories tmp-filter-substrate -m "Import Substrate" -q $SIGN_ARGS
git merge --allow-unrelated-histories tmp-filter-polkadot -m "Import Polkadot" -q $SIGN_ARGS
git merge --allow-unrelated-histories tmp-filter-cumulus -m "Import Cumulus" -q $SIGN_ARGS
echo "Imported Substate $COMMIT_SUB"
echo "Imported Polkadot $COMMIT_DOT"
echo "Imported Cumulus  $COMMIT_CUM"

# Otherwise we have two crates named `pallet-template`.
# rm -rf cumulus/parachain-template/pallets/template/Cargo.toml
# git add -u
# git commit -m "Remove duplicate template pallet" $SIGN_ARGS

# FIXME These crates need to be fix upstream before doing the monorepo migration:
# sed 's|\[workspace\]||g' -i substrate/frame/election-provider-multi-phase/test-staking-e2e/Cargo.toml
# sed 's|\[workspace\]||g' -i substrate/scripts/ci/node-template-release/Cargo.toml
# sed 's|\[workspace\]||g' -i polkadot/erasure-coding/fuzzer/Cargo.toml
# sed 's|0.8|0.16|g' -i substrate/scripts/ci/node-template-release/Cargo.toml
sed 's|../../Cargo.toml|../../../Cargo.toml|g' -i  cumulus/test/relay-validation-worker-provider/build.rs

#Fix docify
find substrate/frame -type f -not -path target -exec sed -i 's|docify::embed!("|docify::embed!("substrate/|g' {} \;

git add --all
git commit -m "FIXME Hotfix crates" $SIGN_ARGS

rm -rf substrate/Cargo.toml polkadot/Cargo.toml cumulus/Cargo.toml */Cargo.lock
#diener workspacify
git add --all
git commit -m "Clear workspace" $SIGN_ARGS

#echo '
#[workspace.package]
#authors = ["Parity Technologies <admin@parity.io>"]
#edition = "2021"
#repository = "https://github.com/paritytech/polkadot.git"
#version = "0.9.41"' >> Cargo.toml
#
#git add --all && git commit -m "Fix Workspace" $SIGN_ARGS

echo "Running sanity checks..."
COMMITS=$(git log --no-merges -M --oneline --follow -- substrate/README.md | wc -l)
if [ "$COMMITS" -ne "35" ]; then
	echo "Wrong number of commits, got $COMMITS"
fi
COMMITS=$(git log --no-merges -M --oneline --follow -- polkadot/README.md | wc -l)
if [ "$COMMITS" -ne "51" ]; then
	echo "Wrong number of commits, got $COMMITS"
fi
COMMITS=$(git log --no-merges -M --oneline --follow -- cumulus/README.md | wc -l)
if [ "$COMMITS" -ne "42" ]; then
	echo "Wrong number of commits, got $COMMITS"
fi

cd ..
rm -rf polkadot-sdk.zip
zip -r polkadot-sdk.zip polkadot-sdk -q
rm -rf polkadot-sdk

echo "All done. Output in polkadot-sdk.zip"
echo "Call the fellowing script like: "
