"""
This script is used to upgrade accounts to the new balance storage scheme
introduced in https://github.com/paritytech/substrate/pull/12951

Install the dependency https://github.com/polkascan/py-substrate-interface like:
 pip install substrate-interface
Then run it:
 python3 upgrade-accounts.py
"""

import json
import os
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

chain = SubstrateInterface(
    url="ws://127.0.0.1:9944",
    # Using the public endpoint can get you rate-limited.
    # url="wss://kusama-rpc.polkadot.io",
    # These Parity internals are not limited.
    #url="wss://kusama-try-runtime-node.parity-chains.parity.io:443"
)

print(f"Connected to {chain.name}: {chain.chain} v{chain.version}")

sender_uri = os.getenv('SENDER_URI', '//Alice')
sender = Keypair.create_from_uri(sender_uri, ss58_format=chain.ss58_format)
print(f"Using sender account {sender.ss58_address}")


def main():
    """
    […] run though all accounts with reserved/locked funds on the system and call a
    particular transaction on them
    """
    accounts = []
    block = chain.get_chain_finalised_head()
    print(f"Using block {block}")
    account_query = chain.query_map('System', 'Account', page_size=1000, block_hash=block)

    for (i, (id, info)) in enumerate(account_query):
        account = info['data']
        frozen = account['frozen'].value
        reserved = account['reserved'].value
        is_new_logic = ((account['flags'].value & 0x80000000000000000000000000000000) != 0)

        if (not is_new_logic):
            accounts.append(id.value)

        if i % 5000 == 0 and i > 0:
            percent = round((100 * len(accounts)) / (i + 1), 2)
            print(
                f"Checked {i} accounts; {len(accounts)} ({percent} %) eligible")

    print(f"Found {len(accounts)} eligible accounts in total")

    out_file = f"upgradable-accs-{chain.chain}.json"
    with open(out_file, 'w') as f:
        json.dump(accounts, f)
        print(f"Wrote accounts to '{out_file}'")

    # How many accounts each call should upgrade.
    accs_per_call = 64
    weight_second = 1e12
    decimals = chain.token_decimals or 0

    for (i, chunk) in enumerate(chunks(accounts, accs_per_call)):
        call = chain.compose_call(
            call_module='Balances',
            call_function='upgrade_accounts',
            call_params={
                'who': chunk,
            }^
        )
        extrinsic = chain.create_signed_extrinsic(call=call, keypair=sender, era={'period': 100})
        print(f"Extrinsic {i + 1}: upgrading {len(chunk)} accounts of {(i + 1) * accs_per_call} total ({round((100 * (i + 1) * accs_per_call) / len(accounts), 2):.2f}) %")

        try:
            receipt = chain.submit_extrinsic(
                extrinsic, wait_for_inclusion=True)
            print(f"Extrinsic included in block {receipt.block_hash}: "
                  f"consumed {receipt.weight['ref_time'] / weight_second} seconds of weight and "
                  f"paid {(receipt.total_fee_amount or 0) / 10**decimals} {chain.token_symbol}")
            events = receipt.triggered_events
            # Search for the Balances::Upgraded event.
            good_events = 0
            for event in events:
                event = event['event'].value
                if event['module_id'] == 'Balances' and event['event_id'] == 'Upgraded':
                    good_events += 1
            if good_events != len(chunk):
                print(f"WARNING: Expected {len(chunk)} Upgraded events, but got {good_events}")
            if good_events < len(chunk) * 0.90:
                print(f"ERROR: Expected at least {len(chunk) * 0.90} Upgraded events, but got {good_events}")
                exit(1)
            print(f"Successfully upgraded {len(chunk)} accounts, success rate {100 * good_events / len(chunk):.2f}%")
        except SubstrateRequestException as e:
            print(f"Failed to submit extrinsic: {e}")
            raise e

def chunks(list, n):
    """
    Lazily split 'list' into 'n'-sized chunks.
    """
    for i in range(0, len(list), n):
        yield list[i:i + n]


if __name__ == "__main__":
    main()
