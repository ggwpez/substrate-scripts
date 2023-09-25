#!/usr/bin/env bash

set -eo pipefail

# First arg is the CWD.
MONO_REPO=$1
RUNTIMES_REPO=$2
TAG="v1.1.0-rc2"

if [ -z "$MONO_REPO" ] || [ -z "$RUNTIMES_REPO" ]; then
	echo "Usage: ./fellowship.sh <MONO_REPO> <RUNTIMES_REPO> <COMMIT>"
	exit 1
fi

cd $MONO_REPO
git checkout -- . && git checkout $TAG
COMMIT=$(git rev-parse HEAD)

cd ../$RUNTIMES_REPO
git add --all && git stash push && git stash drop || true
# This is the master commit right before the PR this MR was created:
git checkout bf6da3ce9eb100b88a30a904ffe2e3389cdacd70
git branch -D oty-import-$TAG || true
git checkout -b oty-import-$TAG
cd ..

mkdir -p $RUNTIMES_REPO/system-parachains/glutton/glutton-kusama

cp -R $MONO_REPO/cumulus/parachains/runtimes/assets/asset-hub-kusama $RUNTIMES_REPO/system-parachains/asset-hubs/
cp -R $MONO_REPO/cumulus/parachains/runtimes/assets/asset-hub-polkadot $RUNTIMES_REPO/system-parachains/asset-hubs/
cp -R $MONO_REPO/cumulus/parachains/runtimes/bridge-hubs/bridge-hub-kusama $RUNTIMES_REPO/system-parachains/bridge-hubs/
cp -R $MONO_REPO/cumulus/parachains/runtimes/bridge-hubs/bridge-hub-polkadot $RUNTIMES_REPO/system-parachains/bridge-hubs/
cp -R $MONO_REPO/cumulus/parachains/runtimes/collectives/collectives-polkadot $RUNTIMES_REPO/system-parachains/collectives/
cp -R $MONO_REPO/cumulus/parachains/runtimes/glutton/glutton-kusama $RUNTIMES_REPO/system-parachains/glutton/
cp -R $MONO_REPO/polkadot/runtime/kusama $RUNTIMES_REPO/relay/
cp -R $MONO_REPO/polkadot/runtime/polkadot $RUNTIMES_REPO/relay/

cd $RUNTIMES_REPO

git add --all
git commit -m "Import Polkadot-SDK $TAG (${COMMIT:0:10})" $SIGN_ARGS

CHECK_1='216db9755a5ebfdc5a61066cf9770847776ea320'
if [[ $(git diff --stat $CHECK_1) != "" ]]; then
	echo "FAILED TO REPRODUCE CHECKPOINT ${CHECK_1:0:10}"
	exit 1
else
	echo "✅ REPRODUCED CHECKPOINT ${CHECK_1:0:10}"
fi

git mv system-parachains/glutton/ system-parachains/gluttons/

git add --all
git commit -m "Rename glutton to gluttons" $SIGN_ARGS

CHECK_2='432d49bab919fca7862255754888a2c39586c7ba'
if [[ $(git diff --stat $CHECK_2) != "" ]]; then
	echo "FAILED TO REPRODUCE CHECKPOINT ${CHECK_2:0:10}"
	exit 1
else
	echo "✅ REPRODUCED CHECKPOINT ${CHECK_2:0:10}"
fi

if [[ ! -f "../lgtm.4ce14735e0a3a6a663ed80e73afd1dd0de4167ab" ]]; then
	git diff-tree -p '4ce14735e0a3a6a663ed80e73afd1dd0de4167ab'
	read -p "Please review this patch manually. Looks good to you? (y/n)" -n 1 -r
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		touch '../lgtm.4ce14735e0a3a6a663ed80e73afd1dd0de4167ab'
	else
		exit 1
	fi
else
	echo "Patch already approved in the past"
fi
git diff-tree -p '4ce14735e0a3a6a663ed80e73afd1dd0de4167ab' | git apply
echo "Patch applied"

# Same for commit de16d6f5bd10b2ff8c2a319fe493a9c647c46c3f
if [[ ! -f "../lgtm.de16d6f5bd10b2ff8c2a319fe493a9c647c46c3f" ]]; then
	git diff-tree -p 'de16d6f5bd10b2ff8c2a319fe493a9c647c46c3f'
	read -p "Please review this patch manually. Looks good to you? (y/n) " -n 1 -r
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		touch '../lgtm.de16d6f5bd10b2ff8c2a319fe493a9c647c46c3f'
	else
		exit 1
	fi
else
	echo "Patch already approved in the past"
fi
git diff-tree -p 'de16d6f5bd10b2ff8c2a319fe493a9c647c46c3f' | git apply
echo "Patch applied"

CHECK_3='de16d6f5bd10b2ff8c2a319fe493a9c647c46c3f'
if [[ $(git diff --stat $CHECK_3) != "" ]]; then
	echo "FAILED TO REPRODUCE CHECKPOINT ${CHECK_3:0:10}"
	exit 1
else
	echo "✅ REPRODUCED CHECKPOINT ${CHECK_3:0:10}"
fi

# Replace parachain-info with staging-parachain-info
find . -name 'Cargo.toml' -exec perl -i -pe 's/parachain-info \= {/parachain-info = { package = "staging-parachain-info",/g' {} +

git add --all
git commit -m "Replace parachain-info with staging-parachain-info" $SIGN_ARGS

CHECK_4='56b95fb7d0ab1f60907debbc0afe266adcccd955'
if [[ $(git diff --stat $CHECK_4) != "" ]]; then
	echo "FAILED TO REPRODUCE CHECKPOINT ${CHECK_4:0:10}"
	exit 1
else
	echo "✅ REPRODUCED CHECKPOINT ${CHECK_4:0:10}"
fi

cd ..
echo "🏋️ Updating dependencies to use crates-io ... (takes a while)"
touch .crates-io-cache.txt
cargo r -q --manifest-path fix-deps/Cargo.toml -- runtimes/

cd $RUNTIMES_REPO
git add --all
git commit -m "Update dependencies to use crates-io" $SIGN_ARGS

CHECK_5='06de008bb530bd61693d750f23baa17f0ee7c238'
if [[ $(git diff --stat $CHECK_5) != "" ]]; then
	echo "FAILED TO REPRODUCE CHECKPOINT ${CHECK_5:0:10}"
	exit 1
else
	echo "✅ REPRODUCED CHECKPOINT ${CHECK_5:0:10}"
fi

# Some sanity checking of the deps:
python3 -m pip install toml
python3 ../check-deps.py $PWD

cp ../$MONO_REPO/Cargo.lock .
echo "Compiling runtimes ..."
cargo b -r -q --workspace --all-targets --all-features --target-dir ../target

git add --all
git commit -m "Generate lockfile" $SIGN_ARGS

CHECK_6='37ef1da4fe30cd77b3ca185a9dd4da922143f983'
if [[ $(git diff --stat $CHECK_6) != "" ]]; then
	echo "FAILED TO REPRODUCE CHECKPOINT ${CHECK_6:0:10}"
	exit 1
else
	echo "✅ REPRODUCED CHECKPOINT ${CHECK_6:0:10}"
fi

echo "Runtimes compiled."

BRANCH="origin/oty-import-$TAG"
if [[ $(git diff $BRANCH --stat) != "" ]]; then
	echo "DIFF TO REMOTE IS NOT EMPTY"
	exit 1
else
	echo "✅ FINAL CHECK PASSED. EMPTY DIFF TO REMOTE '$BRANCH'"
fi

cd ..
LOCKS=$(sha256sum -c runtime-hashlocks.txt)
if [[ $LOCKS != *"OK"* ]]; then
	# Just a warning in this case:
	sha256sum -c runtime-hashlocks.txt || true
	echo "⚠⚠⚠ WASM RUNTIME HASHES MITMATCH ⚠⚠⚠\nThis may be acceptible since the code was checked to match. Otherwise retry with latest Rust Stable 1.72."
else
	echo "✅ Final advisory check passed; WASM blob hashes match."
fi
