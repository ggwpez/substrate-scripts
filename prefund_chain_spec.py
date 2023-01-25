import json
import random
import argparse

from substrateinterface import Keypair
from substrateinterface.utils.ss58 import ss58_encode

def main(args):
    spec = None
    args = parse_args(args)

    with open(args.input) as f:
        spec = json.load(f)
        for i in range(args.n):
            account = generate_pk(i, args.uri)
            spec["genesis"]["runtime"]["balances"]["balances"].append([account, 1000000000000000000000])
            print("Progress %:", round(100 * i / args.n))
    
    with open(args.o, 'w') as f:
        json.dump(spec, f, indent=4)
    print(f'Added {args.n} accounts to {args.o}')

def parse_args(raw):
    args = argparse.ArgumentParser()
    # input file positional
    args.add_argument("input", type=str, help="Input file")
    args.add_argument("-n", type=int, default=10000, help="Number of accounts to add")
    args.add_argument("-o", type=str, default="out-spec.json", help="Output file")
    args.add_argument("--uri", type=str, default=None, help="URI to derive accounts from. Will append //index to it.")
    args.add_argument("--amount", type=int, default=1000000000000000000000, help="Amount in Plank to fund each account with")
    return args.parse_args(args=raw)

def generate_pk(index, maybe_uri):
    """
    Generates a new account from a given URI by appending //{index} or a random one.
    Random ones are much faster to generate than deriving, so only use the URI if you
    really need to control the accounts.
    """
    if maybe_uri:
        return Keypair.create_from_uri(f"{maybe_uri}//{index}").ss58_address
        
    id = random.getrandbits(256).to_bytes(32, 'big')
    return ss58_encode(id, 42)

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
