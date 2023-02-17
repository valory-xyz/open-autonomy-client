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
async def test_downloader(downloader_class: Callable):
    dl = downloader_class()
    await dl.download(demo_urls)


if __name__ == "__main__":
    pytest.main([__file__])
