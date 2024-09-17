#!/bin/bash

while true;
do
	npm start
	node votable.js 15r3tauLe4n8pRb9EzNVvdzbKc15rjscW8z2rzTRBGPwU4wh --all-tracks --rpc="wss://rpc.polkadot.io" --pallet referenda
	echo "😴"
	sleep 3600
done
