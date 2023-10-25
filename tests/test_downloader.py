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


"""Tests the downloader."""


from typing import Callable

import pytest

from open_autonomy_client.downloader import (
    AllInParallelDownloader,
    SimpleDownloader,
    SmartDownloader,
    SomeFirstDownloader,
)

demo_urls = [
    "https://api.drand.sh/8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce/public/latest",
    "https://api2.drand.sh/8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce/public/latest",
    "https://api3.drand.sh/8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce/public/latest",
    "https://drand.cloudflare.com/8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce/public/latest",
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "downloader_class",
    [SimpleDownloader, AllInParallelDownloader, SomeFirstDownloader, SmartDownloader],
)
async def test_downloader_real_links(downloader_class: Callable) -> None:
    """Test the downloader using the demo urls."""
    downloader = downloader_class()
    await downloader.download(demo_urls)


if __name__ == "__main__":
    pytest.main([__file__])
