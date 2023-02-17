from hashlib import sha256
from typing import List
from unittest.mock import patch

import pytest
from eth_account import Account

from open_autonomy_client.client import Client


def generate_key() -> Account:
    account = Account.create(b"some")  # pylint: disable=no-value-for-parameter
    return account


def make_data_signature(key, data) -> str:
    hash_hex = sha256(data.encode("ascii")).hexdigest()
    signature = key.signHash(hash_hex)
    return signature.signature.hex()[2:]  # cut 0x prefix


def make_url_data_response(data: str, keys: List[Account]):
    return {
        "payload": data,
        "signatures": {key.address: make_data_signature(key, data) for key in keys},
    }


@pytest.mark.asyncio
async def test_client():
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
    assert data_fetched == sample_payload


if __name__ == "__main__":
    pytest.main([__file__])
