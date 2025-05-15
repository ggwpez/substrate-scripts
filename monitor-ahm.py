import os
import json
import math
import time
import argparse

from dotenv import load_dotenv
import numpy as np

MAX = 4600 # Number of messages we expect to see

from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

chain = SubstrateInterface(
	url="wss://westend-asset-hub-rpc.polkadot.io",
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")
last_value = 0

key = chain.create_storage_key('AhMigrator', 'DmpDataMessageCounts')

def subscription_handler(_storage_key, updated_obj, _update_nr, _subscription_id):
	global last_value

	(n, _) = updated_obj.value
	percent = n / MAX * 100
	
	if n == last_value:
		return
	last_value = n
	
	print(f"Progress {percent:.2f}%")
	os.system(f"osascript -e 'display notification \"{percent:.2f}%\" with title \"! AHM progress\" sound name \"Glass\"'")

result = chain.subscribe_storage(
	storage_keys=[key], subscription_handler=subscription_handler
)
