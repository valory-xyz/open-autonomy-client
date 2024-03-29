#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------


"""Tests for the Client."""


import json
from hashlib import sha256
from typing import Any, Dict, List, Union, cast
from unittest.mock import patch

import pytest
from eth_account import Account

from open_autonomy_client.client import Client


def generate_key() -> Account:
    """Generate an account."""
    account = Account.create(b"some")  # pylint: disable=no-value-for-parameter
    return account


def make_data_signature(key: Account, data: str) -> str:
    """Get the signature of the given key on the given data."""
    hash_hex = sha256(data.encode("ascii")).hexdigest()
    signature = key.signHash(hash_hex)
    return signature.signature.hex()[2:]  # cut 0x prefix


def make_url_data_response(data: str, keys: List[Account]) -> Dict[str, Any]:
    """Create a dummy response."""
    return {
        "payload": data,
        "signatures": {key.address: make_data_signature(key, data) for key in keys},
    }


@pytest.mark.asyncio
async def test_client_data_generated() -> None:
    """Test client with generated data."""
    num_agents = 5
    sample_payload = '{"some": "data"}'
    priv_keys = [generate_key() for _ in range(num_agents)]

    urls_list = [f"http://host{i}.com" for i in range(num_agents)]
    pub_keys_list = [i.address for i in priv_keys]

    url_data_response = make_url_data_response(sample_payload, priv_keys)
    url_data_responses = {url: url_data_response for url in urls_list}
    client = Client(urls=urls_list, keys=pub_keys_list)
    with patch.object(client, "_fetch_data_from_urls", return_value=url_data_responses):
        data_fetched = await client.fetch()
    assert data_fetched == json.loads(sample_payload)


DATA_FROM_AGENT: Dict[str, Union[str, Dict[str, str]]] = {
    "payload": "{"
    '"agent_address": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65", '
    '"data_source": "coinbase", '
    '"estimate": 23880.12, '
    '"observations": {"0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65": 0.0}, '
    '"period_count": 1, '
    '"prev_tx_hash": "0x107b04e16a31b37a2e81ba3ad5de338a703d5d7ea96768ac46f6dfa38050b657", '
    '"unit": "BTC:USD"'
    "}",
    "signatures": {
        "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65": "e12987455818cd3c37952ff7e15bc11a86d10b5ac46"
        "bfe58fba7072c2a44a706205fdd4a9c9c2d29caa9a9"
        "888d0b7cc0e63c13f7bb82c56e634aaa80259145f11c"
    },
}


@pytest.mark.asyncio
async def test_client_data_from_agent_example() -> None:
    """Test client with example data."""
    sample_payload = cast(str, DATA_FROM_AGENT["payload"])
    sample_signatures = cast(Dict[str, str], DATA_FROM_AGENT["signatures"])

    url = "http://hostsome.com"
    urls_list = [url]

    pub_keys_list = list(sample_signatures.keys())
    url_data_response = DATA_FROM_AGENT
    url_data_responses = {url: url_data_response}
    client = Client(urls=urls_list, keys=pub_keys_list)
    with patch.object(client, "_fetch_data_from_urls", return_value=url_data_responses):
        data_fetched = await client.fetch()
    assert data_fetched == json.loads(sample_payload)


if __name__ == "__main__":
    pytest.main([__file__])
