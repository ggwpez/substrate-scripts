#!/usr/bin/env bash

set -eox pipefail

# First arg is the CWD.
MONO_REPO=$1
RUNTIMES_REPO=$2
TAG="v1.1.0-rc2"

# Error if any of these are empty.
if [ -z "$MONO_REPO" ] || [ -z "$RUNTIMES_REPO" ]; then
	echo "Usage: ./fellowship.sh <MONO_REPO> <RUNTIMES_REPO> <COMMIT>"
	exit 1
fi

cd $MONO_REPO
git checkout -- . && git checkout $TAG
COMMIT=$(git rev-parse HEAD)

cd ../$RUNTIMES_REPO
git add --all && git stash push && git stash drop || true
git checkout main
git branch -D oty-import-$TAG || true
git checkout -b oty-import-$TAG
cd ..

SIGN_ARGS="--signoff --no-gpg-sign"

mkdir -p $RUNTIMES_REPO/system-parachains/glutton/glutton-kusama

cp -R $MONO_REPO/cumulus/parachains/runtimes/assets/asset-hub-kusama $RUNTIMES_REPO/system-parachains/asset-hubs/
cp -R $MONO_REPO/cumulus/parachains/runtimes/assets/asset-hub-polkadot $RUNTIMES_REPO/system-parachains/asset-hubs/
cp -R $MONO_REPO/cumulus/parachains/runtimes/bridge-hubs/bridge-hub-kusama $RUNTIMES_REPO/system-parachains/bridge-hubs/
cp -R $MONO_REPO/cumulus/parachains/runtimes/bridge-hubs/bridge-hub-polkadot $RUNTIMES_REPO/system-parachains/bridge-hubs/
cp -R $MONO_REPO/cumulus/parachains/runtimes/collectives/collectives-polkadot $RUNTIMES_REPO/system-parachains/collectives/
cp -R $MONO_REPO/cumulus/parachains/runtimes/glutton/glutton-kusama $RUNTIMES_REPO/system-parachains/gluttons/
cp -R $MONO_REPO/polkadot/runtime/kusama $RUNTIMES_REPO/relay/
cp -R $MONO_REPO/polkadot/runtime/polkadot $RUNTIMES_REPO/relay/

cd $RUNTIMES_REPO

git add --all
# only print the first 10 chars of the commit
git commit -m "Import Polkadot-SDK $TAG (${COMMIT:0:10})" $SIGN_ARGS

# TODO fixup crates.io dependencies
