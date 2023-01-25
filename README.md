# Setup

```sh
pip install substrate-interface
# or
pip install -r requirements.txt
```

# Content

[prefund-chain-spec.py](prefund-chain-spec.py): can be used to prefund accounts in a Substrate chainspec. Example:  
```sh
./target/release/substrate build-spec --dev > spec.json
python prefund-chain-spec.py
./target/release/substrate --chain=out-spec.json --alice --force-authoring --tmp --no-hardware-benchmarks
```
