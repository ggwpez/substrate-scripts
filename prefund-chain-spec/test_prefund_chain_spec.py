import os
import json
import pytest
import prefund_chain_spec

@pytest.mark.parametrize("chain", ["dev", "polkadot-dev", "kusama-dev", "westend-dev", "rococo-dev"])
def test_prefund_works(chain):
    input = f'{chain}.json'
    output = f'{chain}-out.json'

    # Generate a chain spec
    os.system(f'./polkadot build-spec --chain=dev > {input}')
    assert prefund_chain_spec.main([input, "-n", "100", "--uri", "//Alice", "-o", output]) == None
    # Check that `out.json` exists
    assert os.path.exists(input) == True
    # Check that it has 400 lines more than the original spec (4 for each acc).
    assert len(open(input).readlines()) + 400 == len(open(output).readlines())
    # Check that `spec.json` is a valid JSON file:
    with open(output) as f:
        json.load(f)
