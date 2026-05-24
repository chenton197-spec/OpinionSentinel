from __future__ import annotations

from abc import ABC, abstractmethod


class SourceAdapter(ABC):
    source_name: str

    @abstractmethod
    def fetch_list(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def fetch_detail(self, item: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw_detail: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def extract_publish_time(self, raw_detail: dict) -> str:
        raise NotImplementedError

    @abstractmethod
    def build_fingerprint(self, normalized_detail: dict) -> str:
        raise NotImplementedError
