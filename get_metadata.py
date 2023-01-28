import json
import sys

from substrateinterface import SubstrateInterface

URL = "wss://kusama-rpc.polkadot.io:443"
substrate = SubstrateInterface(URL)

query = substrate.rpc_request(
	"state_getMetadata", None
)
with open("metadata.json", "w") as f:
	f.write(json.dumps(query, indent=4))
