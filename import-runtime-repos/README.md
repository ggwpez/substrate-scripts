# Import for the Polkadot Fellowship
Contains the import logic for [MR#1](https://github.com/polkadot-fellows/runtimes/pull/1).

First create a temporary folder and run the `monorepo.sh` script like: `./monorepo.sh tmp/`.  
This will produce a `polkadot-sdk.zip` that contains Substrate, Polkadot and Cumulus in one.  
This can be ingested by the `fellowship.sh` script by running it on the same folder: `./fellowship.sh tmp/`. As output you get a `polkadot-sdk.filtered` folder that contains the final runtimes result.
