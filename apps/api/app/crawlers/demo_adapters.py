from hashlib import sha1

from app.crawlers.base import SourceAdapter


class DemoNewsAdapter(SourceAdapter):
    source_name = "news-portal"

    def fetch_list(self) -> list[dict[str, str]]:
        return [{"url": "https://news.example.com/cloud-incident", "title": "云服务中断事件"}]

    def fetch_detail(self, item: dict[str, str]) -> dict[str, str]:
        return {**item, "content": "示例内容", "published_at": "2026-05-24T11:10:00+08:00"}

    def normalize(self, payload: dict[str, str]) -> dict[str, str]:
        return payload

    def extract_publish_time(self, payload: dict[str, str]) -> str:
        return payload["published_at"]

    def build_fingerprint(self, payload: dict[str, str]) -> str:
        return sha1(payload["url"].encode("utf-8")).hexdigest()
