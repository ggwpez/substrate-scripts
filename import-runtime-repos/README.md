# Import for the Polkadot Fellowship
Contains the import logic for [MR#1](https://github.com/polkadot-fellows/runtimes/pull/1).

First clone the `runtimes` repo:  
```bash
git clone https://github.com/polkadot-fellows/runtimes
```

Then run the [import-repos.sh](./import-repos.sh) script. This required `python3` to be installed. The generated commits are not signed.  

The [check-deps.py](./check-deps.py) will probably fail if new crates got added. That script is to safeguard workspace imports so that we dont actually depend on external deps instead of local ones.
