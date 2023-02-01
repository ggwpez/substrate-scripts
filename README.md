# Setup

```sh
pip install substrate-interface
# or
pip install -r requirements.txt
```

# Content

**[prefund-chain-spec](/prefund-chain-spec/)**: can be used to prefund accounts in a Substrate chainspec. Example:  
```sh
./target/release/substrate build-spec --dev > spec.json
python prefund-chain-spec.py
./target/release/substrate --chain=out-spec.json --alice --force-authoring --tmp --no-hardware-benchmarks
```

Tests with:
```sh
pytest prefund-chain-spec
```

**[update-weights](update-weights/)**: Helper script to run all pallet benchmarks in Substrate/Polkadot/Cumulus.  

Usage like (see [README](update-weights/README.md)):
```bash
python run.py --debug --project substrate --cwd ~/work/substrate/
```
