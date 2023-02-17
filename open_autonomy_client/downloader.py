import asyncio
import random
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, suppress
from typing import Dict, List, Tuple, Union

import aiohttp


class BaseDownloader(ABC):
    async def _download_from_url(self, url: str) -> Union[Dict, Exception]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    body = await resp.json()
            return body
        except Exception as e:
            return e

    def is_good_response(self, resp: Union[Exception, Dict]) -> bool:
        return not isinstance(resp, BaseException)

    def filter_responses(
        self, url_responses: Dict[str, Union[Dict, Exception]]
    ) -> Tuple[Dict[str, Union[Dict, Exception]], Dict[str, Union[Dict, Exception]]]:
        good = {}
        bad = {}
        for url, resp in url_responses.items():
            if self.is_good_response(resp):
                good[url] = resp
            else:
                bad[url] = resp
        return good, bad

    @abstractmethod
    async def download(self, urls: List[str]) -> Dict[str, Union[Dict, Exception]]:
        raise NotImplementedError


class SimpleDownloader(BaseDownloader):
    async def download(self, urls: List[str]) -> Dict[str, Union[Dict, Exception]]:
        return {url: await self._download_from_url(url) for url in urls}


class AllInParallelDownloader(BaseDownloader):
    async def download(self, urls: List[str]) -> Dict[str, Union[Dict, Exception]]:
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


class SmartDownloader(BaseDownloader):
    """
    Downloader allows to:
        * concurrent_requests = 1 - download one by one
        * concurrent_requests = 0 - all in parallel
        * concurrent_requests = n>1 - download in n tasks
        * stop on first result - return when the first non error respose downloaded.
    """

    def __init__(self, concurrent_requests: int = 2, stop_on_first_result: bool = True):
        self._concurrent_requests = concurrent_requests
        self._stop_on_first_result = stop_on_first_result

    async def _worker(self, in_queue: asyncio.Queue, out_queue: asyncio.Queue):
        """Get url from in queue and put result to out queue"""
        while not in_queue.empty():
            url = await in_queue.get()
            try:
                result = await self._download_from_url(url)
                await out_queue.put((url, result))
            except asyncio.CancelledError as e:
                await out_queue.put((url, e))
                raise
            except Exception as e:
                await out_queue.put((url, e))

    @asynccontextmanager
    async def _workers_ctx(
        self, urls: List[str], num: int = 0
    ) -> Tuple[asyncio.Queue, asyncio.Queue]:
        try:
            num = num or len(urls)
            num = min(num, len(urls))

            in_queue = asyncio.Queue()
            for url in urls:
                await in_queue.put(url)
            out_queue = asyncio.Queue()

            workers = set(
                [
                    asyncio.ensure_future(self._worker(in_queue, out_queue))
                    for i in range(num)
                ]
            )

            yield (
                in_queue,
                out_queue,
            )
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
        results = {}

        async with self._workers_ctx(urls, num=self._concurrent_requests) as (
            in_queue,
            out_queue,
        ):
            while not in_queue.empty():
                url, result = await out_queue.get()
                results[url] = result
                if self._stop_on_first_result and self.is_good_response(result):
                    # got result with non expcetion reponse, stop it
                    break

        # set pending urls to cancelled
        while not in_queue.empty():
            url = await in_queue.get()
            results[url] = asyncio.CancelledError(
                "cancelled cause first good results recevied"
            )

        good, _ = self.filter_responses(results)
        return good if good else results
