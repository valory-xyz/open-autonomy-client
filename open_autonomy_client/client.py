import asyncio
import json
from hashlib import sha256
from itertools import groupby
from typing import Any, Dict, List, Union

from eth_account._utils.signing import to_standard_signature_bytes
from eth_account.datastructures import HexBytes
from eth_keys.main import Signature

from open_autonomy_client.downloader import SmartDownloader


class SignatureChecker:
    """Signagure checker."""

    hash_algo = sha256

    @classmethod
    def check(cls, key_str: str, signature_str: str, data_bytes: bytes) -> None:
        """
        Check signature for payload and public key(address) provided.

        :param key_str: str, pub key or agent address
        :param signature_str: hex encoded signature byte string
        :param data_bytes: data signature created for.

        :raises ValueError: if signature verification failed.
        """
        key_addr = cls._load_key(key_str)
        signature = cls._load_signature(signature_str)
        data_hash = cls._get_data_hash(data_bytes)
        recovered_key_address = signature.recover_public_key_from_msg_hash(
            data_hash
        ).to_checksum_address()
        recovered_key_address = recovered_key_address.lower()
        if recovered_key_address != key_addr:
            raise ValueError(
                f"signature verification failed for key: {key_addr}, recovered key is {recovered_key_address}"
            )

    @classmethod
    def _load_key(cls, key_str: str) -> str:
        """Load key string.

        :param key_str: str, pub key or agent address

        :return: str
        """
        return key_str.lower()

    @classmethod
    def _load_signature(cls, signature_str: str) -> Signature:
        """
        Load signature from hex string.

        :param signature_str: hex encoded signature byte string

        :return: signature object
        """
        signature_bytes_standard = to_standard_signature_bytes(
            HexBytes(bytes.fromhex(signature_str))
        )
        return Signature(signature_bytes=signature_bytes_standard)

    @classmethod
    def _get_data_hash(cls, data_bytes: bytes) -> bytes:
        """
        Get data hash for data.

        :param data_bytes: data signature created for.

        :return: hash digest in bytes
        """
        return cls.hash_algo(data_bytes.encode("ascii")).digest()


class Client:
    """
    Open autonomy client.

    Fetch data from multiple agents by http, check signatures.
    """

    def __init__(self, urls: List[str], keys: List[str], **downloader_kwargs) -> None:
        """
        Init client.

        :param urls: list of urls
        :param keys: list of agents addresses
        :param downloader_kwargs: kwars to pass to downloader instance

        :raises ValueError: Amount of urls and keys has to match!
        """
        if len(urls) != len(keys):
            raise ValueError("Amount of urls and keys has to match!")

        self._urls = urls
        self._keys = self._fix_keys(keys)
        self._downloader = self._get_downloader(**downloader_kwargs)

    def _fix_keys(self, keys: List[str]) -> List[str]:
        """
        Make keys string lower case.

        :param keys: list of pub keys/addresses

        :return: list of strings
        """
        return [i.lower() for i in keys]

    def _get_downloader(self, **kwargs):
        """
        Get downloader instance.

        :param kwargs: downloader constructor kwargs.
        :return: downloader instsance.
        """
        kwargs["stop_on_first_result"] = kwargs.get("stop_on_first_result", False)
        kwargs["concurrent_requests"] = kwargs.get("concurrent_requests", 2)
        return SmartDownloader(**kwargs)

    async def _fetch_data_from_urls(self) -> Dict[str, Union[Dict, Exception]]:
        """
        Fetch data using downloader.

        :return: dict of url, dict json responses.
        :raises ValueError: if download errors
        """
        fetched_urls = await self._downloader.download(self._urls)
        good, bad = self._downloader.filter_responses(fetched_urls)
        if bad:
            raise ValueError(f"Downloads errors: {bad}")
        return good

    def _check_signatures(self, urls_data: Dict[str, Dict]) -> None:
        """
        Check signatures for data downloaded.

        :param urls_data: Dict[str, Dict of json data]
        """
        for url, data in urls_data.items():
            self._check_data_signatures(data)

    def _check_data_signatures(self, data: str):

        payload = self._get_payload_from_data(data)
        signatures = self._get_signatures_from_data(data)

        # check signatures keys, match registered keys
        signatures_not_present = set(self._keys) - set(signatures.keys())
        if signatures_not_present:
            raise ValueError(f"No signatures found for keys: {signatures_not_present}")

        for key, signature in signatures.items():
            self._verify_signature(key, signature, payload)

    def _verify_signature(self, key_str: str, signature_str: str, data: str) -> None:
        """
        Perform signature verification.

        :param key_str: str, pub key or agent address
        :param signature_str: hex encoded signature byte string
        :param data: data signature created for.
        """
        SignatureChecker.check(
            key_str=key_str, signature_str=signature_str, data_bytes=data
        )

    def _check_payload_the_same(self, urls_data: Dict[str, str]) -> None:
        """
        Ensure payload the same for every url response.

        :param urls_data: Dict[str, Dict of json data]

        :raises ValueError: if payloads differ
        """
        # TODO: hashes?, but need recalculate manually
        groups = list(
            groupby(
                sorted(
                    urls_data.items(), key=lambda x: self._get_payload_from_data(x[1])
                ),
                key=lambda x: self._get_payload_from_data(x[1]),
            )
        )
        if len(groups) != 1:
            # TODO: show better details with groups of urls
            raise ValueError("payload differs")

    def _get_payload_from_data(self, url_data: Dict) -> str:
        """
        Get payload from data.

        :param url_data: json decoded dict.

        :return: str
        """
        return url_data["payload"]

    def _get_signatures_from_data(self, url_data: Dict) -> Dict[str, str]:
        """
        Get sifnatures dict from data.

        :param url_data: json decoded dict.

        :return: str
        """
        return url_data["signatures"]

    def _decode_payload(self, payload: str) -> Dict:
        """
        Decode payload.

        :param payload: str

        :return: dict
        """
        return json.loads(payload)

    async def fetch(self) -> Dict:
        """
        Fetch data from urls and check sigantures.

        :return: dict with service state data
        """
        urls_data = await self._fetch_data_from_urls()
        self._check_payload_the_same(urls_data)
        self._check_signatures(urls_data)
        return self._decode_payload(
            self._get_payload_from_data(list(urls_data.values())[0])
        )

    def fetch_sync(self) -> Dict:
        """
        Fetch data from urls and check sigantures.

        :return: dict with service state data
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.fetch())
