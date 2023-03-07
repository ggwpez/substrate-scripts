#!/bin/bash

EXE=$1
REPS=$2
DATA="data-$REPS"

rm -rf $DATA
mkdir $DATA

for i in {1..100};
do
	$1 benchmark pallet --dev --execution=wasm --wasm-execution=compiled --heap-pages=4096 --steps=50 --repeat=$REPS --no-storage-info --pallet='pallet_state_trie_migration' --extrinsic='migrate_custom_child_success' --json-file="$DATA/$i.json" 2>&1 | grep "Time ~="
done
