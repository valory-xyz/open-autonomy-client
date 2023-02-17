from hashlib import sha256
from itertools import groupby
from typing import Any, Dict, List

from eth_account._utils.signing import to_standard_signature_bytes
from eth_account.datastructures import HexBytes
from eth_keys.main import Signature
from open_autonomy_client.downloader import (
    SmartDownloader,
)

class SignatureChecker:
    hash_algo = sha256

    @classmethod
    def check(cls, key_str: str, signature_str: str, data_str: str):
        key_addr = cls._load_key(key_str)
        signature = cls._load_signature(signature_str)
        data_hash = cls._load_data(data_str)
        recovered_key_address = signature.recover_public_key_from_msg_hash(
            data_hash
        ).to_checksum_address()
        assert recovered_key_address == key_addr

    @classmethod
    def _load_key(cls, key_str):
        return key_str

    @classmethod
    def _load_signature(cls, signature_str):
        signature_bytes_standard = to_standard_signature_bytes(
            HexBytes(bytes.fromhex(signature_str))
        )
        return Signature(signature_bytes=signature_bytes_standard)

    @classmethod
    def _load_data(cls, data_str):
        return sha256(data_str.encode("ascii")).digest()


class Client:
    def __init__(self, urls: List[str], keys: List[str]):
        if len(urls) != len(keys):
            raise ValueError("Amount of urls and keys has to match!")

        self._urls = urls
        self._keys = keys

    async def _fetch_data_from_urls(self) -> Dict[str, str]:
        fetched_urls = await SmartDownloader.download(self._urls)
        good, bad = SmartDownloader.filter_responses(fetched_urls)
        if bad:
            raise ValueError(f"Downloads errors: {bad}")
        return good
    
    def _check_signatures(self, urls_data: Dict[str, str]) -> None:
        """Raises exception if something wrong"""
        for url, data in urls_data.items():
            self._check_data_signatures(data)

    def _check_data_signatures(self, data):
        payload = self._get_payload_from_data(data)
        signatures = self._get_signatures_from_data(data)

        # check signatures keys, match registered keys
        signatures_not_present = set(self._keys) - set(signatures.keys())
        if signatures_not_present:
            raise ValueError(f"No signatures found for keys: {signatures_not_present}")

        for key, signature in signatures.items():
            self._verify_signature(key, signature, payload)

    def _verify_signature(self, key_str: str, signature_str: str, data: str) -> None:
        SignatureChecker.check(
            key_str=key_str, signature_str=signature_str, data_str=data
        )

    def _check_payload_the_same(self, urls_data: Dict[str, str]) -> None:
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
        return url_data["payload"]

    def _get_signatures_from_data(self, url_data) -> Dict[str, str]:
        return url_data["signatures"]

    def _decode_payload(self, payload: str) -> Any:
        # TODO: decode json?
        return payload

    async def fetch(self):
        urls_data = await self._fetch_data_from_urls()
        self._check_payload_the_same(urls_data)
        self._check_signatures(urls_data)
        return self._decode_payload(
            self._get_payload_from_data(list(urls_data.values())[0])
        )
