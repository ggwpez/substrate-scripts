#!/bin/bash

while true;
do
	#node convert-bot.js
	npm start
	node votable.js <PK> --all-tracks --rpc="wss://rpc.polkadot.io" --pallet referenda
	echo "😴"
	sleep 3600
done
