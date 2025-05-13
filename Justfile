default:
	chain-spec-builder create -t development --runtime ../polkadot-sdk/target/release/wbuild/westend-runtime/westend_runtime.compact.compressed.wasm named-preset local_testnet
	mv chain_spec.json rc.json
	chain-spec-builder create -t development --relay-chain westend --para-id 2000 --runtime ../polkadot-sdk/target/release/wbuild/asset-hub-westend-runtime/asset_hub_westend_runtime.compact.compressed.wasm named-preset development
	mv chain_spec.json ah.json
	zombienet --provider native spawn ./ahm-zombienet.toml
