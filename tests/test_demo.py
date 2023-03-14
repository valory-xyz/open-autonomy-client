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


"""Tests for the price-oracle demo on staging."""


import pytest

from open_autonomy_client.client import Client

staging_pub_keys_list = [
    "0x77E9b2EF921253A171Fa0CB9ba80558648Ff7215",
    "0x7E07817939c1dBAaBea9Dc56220549539DE1aFC6",
    "0xB51D93A8A1E67c3Db8f9dE5ff89BB2d6525c6aD0",
    "0x91B22F6957fE459e471C52Cdaba1D3c8eC95d2d3",
]


staging_agents_urls_list = [
    f"http://agent-{i}-price-oracle.staging.autonolas.tech"
    for i in range(len(staging_pub_keys_list))
]


@pytest.mark.asyncio
async def test_client_test_demo_staging() -> None:
    """Test the Client with async fetching."""
    client = Client(urls=staging_agents_urls_list, keys=staging_pub_keys_list)
    data_fetched = await client.fetch()
    assert "estimate" in data_fetched


def test_sync_client_test_demo_staging() -> None:
    """Test the Client with sync fetching."""
    client = Client(urls=staging_agents_urls_list, keys=staging_pub_keys_list)
    data_fetched = client.fetch_sync()
    assert "estimate" in data_fetched


if __name__ == "__main__":
    pytest.main([__file__])
