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

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, suppress
from typing import Dict, List, Tuple, Union

import aiohttp


class BaseDownloader(ABC):
    """Base downloader class with basic utility methods."""

    async def _download_from_url(self, url: str) -> Union[Dict, Exception]:
        """
        Download data from url.

        :param url: str

        :return: json decoded dict or exception instance
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    body = await resp.json()
            return body
        except Exception as e:
            return e

    @classmethod
    def is_good_response(cls, resp: Union[Exception, Dict]) -> bool:
        """
        Check response is not exception instance.

        :param resp: dict or exception

        :return: bool
        """
        return not isinstance(resp, BaseException)

    @classmethod
    def filter_responses(
        cls, url_responses: Dict[str, Union[Dict, Exception]]
    ) -> Tuple[Dict[str, Union[Dict, Exception]], Dict[str, Union[Dict, Exception]]]:
        """
        Filter resposnes from url.

        Returns two dicts: one with url: dict for good responses
        another one urls and exceptions

        :param url_responses: dcit with url and responses

        :return: (dict[str, dict], dict[str, exception])
        """
        good = {}
        bad = {}
        for url, resp in url_responses.items():
            if cls.is_good_response(resp):
                good[url] = resp
            else:
                bad[url] = resp
        return good, bad

    @abstractmethod
    async def download(self, urls: List[str]) -> Dict[str, Union[Dict, Exception]]:
        """
        Download data from urls.

        :param urls: list of url strings

        :return: dict of urls and responses(dict or json)
        """
        raise NotImplementedError


class SimpleDownloader(BaseDownloader):
    """Simple downloader, loads data sequentially."""

    async def download(self, urls: List[str]) -> Dict[str, Union[Dict, Exception]]:
        """
        Download data from urls.

        :param urls: list of url strings

        :return: dict of urls and responses(dict or json)
        """
        return {url: await self._download_from_url(url) for url in urls}


class AllInParallelDownloader(BaseDownloader):
    """Download all urls in parallel.."""

    async def download(self, urls: List[str]) -> Dict[str, Union[Dict, Exception]]:
        """
        Download data from urls.

        :param urls: list of url strings

        :return: dict of urls and responses(dict or json)
        """
        task_mapping = {}

        for url in urls:
            task = asyncio.ensure_future(self._download_from_url(url))
            task_mapping[task] = url

        done, pending = await asyncio.wait(
            task_mapping.keys(), return_when=asyncio.ALL_COMPLETED
        )
        assert not pending  # TODO: remove, not needed but for sure
        return {task_mapping[task]: task.result() for task in done}


class SomeFirstDownloader(BaseDownloader):
    """Run in parallel return first good."""

    async def download(self, urls: List[str]) -> Dict[str, Union[Dict, Exception]]:
        """
        Download data from urls.

        :param urls: list of url strings

        :return: dict of urls and responses(dict or json)
        """
        task_mapping = {}

        for url in urls:
            task = asyncio.ensure_future(self._download_from_url(url))
            task_mapping[task] = url

        results = {}
        pending = task_mapping.keys()

        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            if [task for task in done if self.is_good_response(task.result())]:
                # at least one good!
                break

        for task in pending:
            # pending to stop
            task.cancel()

        for task in task_mapping.keys():
            url = task_mapping[task]
            try:
                results[url] = await task
            except (Exception, asyncio.CancelledError) as e:
                results[url] = e

        good, _ = self.filter_responses(results)
        return good if good else results


class _PendingCounter:
    """Utility to count amount of downloads in pending."""

    def __init__(self) -> None:
        """Init."""
        self._counter = 0

    def inc(self) -> None:
        """Increment counter."""
        self._counter += 1

    def dec(self) -> None:
        """
        Decement counter.
        :raises ValueError: if counter is going below 0
        """
        if self._counter == 0:
            raise ValueError("counter can not be dec!")
        self._counter -= 1

    def is_empty(self) -> bool:
        """
        Check counter is 0.

        :return: bool
        """
        return self._counter == 0


class SmartDownloader(BaseDownloader):
    """
    Downloader allows to:
        * concurrent_requests = 1 - download one by one
        * concurrent_requests = 0 - all in parallel
        * concurrent_requests = n>1 - download in n tasks
        * stop on first result - return when the first non error respose downloaded.
    """

    def __init__(
        self, concurrent_requests: int = 2, stop_on_first_result: bool = True
    ) -> None:
        """Init downloader:

        :param concurrent_requests: int, amount of concurent requests
        :param stop_on_first_result: bool, wait for the first success download and stop.
        """
        self._concurrent_requests = concurrent_requests
        self._stop_on_first_result = stop_on_first_result

    async def _worker(
        self,
        in_queue: asyncio.Queue,
        out_queue: asyncio.Queue,
        pending: _PendingCounter,
    ) -> None:
        """
        Get url from in queue and put result to out queue.

        :param in_queue: queue for incoming urls
        :param out_queue: queue for processed urls
        :param pending: pending tasks counter.

        :raises asyncio.CancelledError: asyncio.CancelledError
        """
        while not in_queue.empty():
            url = await in_queue.get()
            pending.inc()
            try:
                result = await self._download_from_url(url)
                await out_queue.put((url, result))
            except asyncio.CancelledError as e:
                await out_queue.put((url, e))
                raise
            except Exception as e:
                await out_queue.put((url, e))
            finally:
                pending.dec()

    @asynccontextmanager
    async def _workers_ctx(
        self, urls: List[str], num: int = 0
    ) -> Tuple[asyncio.Queue, asyncio.Queue, _PendingCounter]:
        """Set worker context.

        set workers and cleanup on content exit

        :param urls: list of urls
        :param num: int, amount of workers
        :yield: in_queue, out_queue, pending_counter.
        """
        try:
            num = num or len(urls)
            num = min(num, len(urls))
            pending = _PendingCounter()
            in_queue = asyncio.Queue()
            for url in urls:
                await in_queue.put(url)
            out_queue = asyncio.Queue()

            workers = set(
                [
                    asyncio.ensure_future(self._worker(in_queue, out_queue, pending))
                    for i in range(num)
                ]
            )

            yield (in_queue, out_queue, pending)
        finally:
            # cancel workers
            for task in workers:
                if not task.done():
                    task.cancel()

            # wait to be cancelled
            await asyncio.wait(workers, return_when=asyncio.ALL_COMPLETED)

            # get results
            for task in workers:
                with suppress(asyncio.CancelledError):
                    await task

    async def download(self, urls: List[str]) -> Dict[str, Union[Dict, Exception]]:
        """
        Download data from urls.

        :param urls: list of url strings

        :return: dict of urls and responses(dict or json)
        """
        results = {}

        async with self._workers_ctx(urls, num=self._concurrent_requests) as (
            in_queue,
            out_queue,
            pending,
        ):
            # do while some in in queue or pending urls
            while not in_queue.empty() or not pending.is_empty():
                url, result = await out_queue.get()
                results[url] = result
                if self._stop_on_first_result and self.is_good_response(result):
                    # got result with non expcetion reponse, stop it
                    break

        # get results from cancelled tasks
        while not out_queue.empty():
            url, result = await out_queue.get()
            results[url] = result

        # set remain urls to cancelled
        while not in_queue.empty():
            url = await in_queue.get()
            results[url] = asyncio.CancelledError(
                "cancelled cause first good results recevied"
            )

        good, _ = self.filter_responses(results)
        return good if good else results
