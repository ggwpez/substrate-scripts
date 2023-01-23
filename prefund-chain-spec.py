import json
import random

from substrateinterface.utils.ss58 import ss58_encode

spec = None
ACCS = 10000
OUT = "out-spec.json"

"""
Reads a 'spec.json' and creates a 'out-spec.json' from it while adding 'ACCS' many pre-
funded accounts. Will not work for Rococo since that uses a slightly different chain-spec
structure.
"""
with open('spec.json') as f:
    spec = json.load(f)
    for i in range(ACCS):
        # Random 32 byte account id
        id = random.getrandbits(256).to_bytes(32, 'big')
        account = ss58_encode(id, 42)
        spec["genesis"]["runtime"]["balances"]["balances"].append(
            [account, 1000000000000000000000])
        # This only works on Substrate branch 'oty-frozen-prefund':
        # reserved = 333333333333333333333 if i % 2 == 0 else 0
        # frozen = 250000000000000000000 if i % 4 == 0 else 0
        # spec["genesis"]["runtime"]["balances"]["balances"].append([account, 1000000000000000000000, reserved, frozen])
        if i % 10000 == 0:
            print("Progress %:", round(100 * i / ACCS))

with open(OUT, 'w') as f:
    json.dump(spec, f, indent=4)
print(f'Wrote {ACCS} accounts to {OUT}')
