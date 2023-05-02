#!/usr/bin/env bash

# Imports Substrate, Polkadot and Cumulus into a new filder. This changes all commit hashes and
# invalidates the signatures, since it re-writes history.

# Deps:
#  python3 -m pip install --user git-filter-repo
#  cargo install diener
# Run:
#  Create some work dir: mkdir ../../tmp
#  ./monorepo.sh ../../tmp

set -ex

# First arg is the CWD.
CWD=$1
# wtf...
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

SIGN_ARGS="--signoff --no-gpg-sign"

cd $CWD

echo "Cloning Polkadot..."
git clone https://github.com/paritytech/polkadot polkadot2 --branch master --quiet
cd polkadot2 && git reset --hard 1d8ccbffd1235d4d1d3a0bf02132d8ea9105078f && cd ..

echo "Cloning Cumulus..."
git clone https://github.com/paritytech/cumulus cumulus2 --branch master --quiet
cd cumulus2 && git reset --hard cd91e6be5f385fab6584842c5fc34514207ca1c5 && cd ..

echo "Cloning Substrate..."
git clone https://github.com/paritytech/substrate substrate2 --branch master --quiet
cd substrate2 && git reset --hard 74b2c92066ec3abcb612faa9272f246ae339fab3 && cd ..

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

mkdir -p monorepo
cd monorepo
git init .
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
rm -rf cumulus/parachain-template/pallets/template/Cargo.toml
git add -u
git commit -m "Remove duplicate template pallet" $SIGN_ARGS

# FIXME These crates need to be fix upstream before doing the monorepo migration:
sed 's|\[workspace\]||g' -i substrate/frame/election-provider-multi-phase/test-staking-e2e/Cargo.toml
sed 's|\[workspace\]||g' -i substrate/scripts/ci/node-template-release/Cargo.toml
sed 's|\[workspace\]||g' -i polkadot/erasure-coding/fuzzer/Cargo.toml
sed 's|0.8|0.16|g' -i substrate/scripts/ci/node-template-release/Cargo.toml
sed 's|../../Cargo.toml|../../../Cargo.toml|g' -i  cumulus/test/relay-validation-worker-provider/build.rs

git add --all
git commit -m "FIXME Hotfix crates" $SIGN_ARGS

rm -rf substrate/Cargo.toml polkadot/Cargo.toml cumulus/Cargo.toml */Cargo.lock
diener workspacify
git add --all
git commit -m "Setup workspace with diener" $SIGN_ARGS

echo '
[workspace.package]
authors = ["Parity Technologies <admin@parity.io>"]
edition = "2021"
repository = "https://github.com/paritytech/polkadot.git"
version = "0.9.41"' >> Cargo.toml

git add -u && git commit -m "Fix Workspace" $SIGN_ARGS

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

echo "Checking dependency resolves..."
python $SCRIPT_DIR/check-deps.py $PWD
echo "Checking build..."
SKIP_WASM_BUILD=1 cargo test "*-runtime" # Build all but only execute 'runtime' tests.

echo "All done"
