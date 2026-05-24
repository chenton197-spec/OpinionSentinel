from __future__ import annotations

from app.crawlers.base import SourceAdapter


class CompanyAnnouncementAdapter(SourceAdapter):
    source_name = "company_announcement"

    def fetch_list(self) -> list[dict]:
        return []

    def fetch_detail(self, item: dict) -> dict:
        return item

    def normalize(self, raw_detail: dict) -> dict:
        return raw_detail

    def extract_publish_time(self, raw_detail: dict) -> str:
        return raw_detail.get("published_at", "")

    def build_fingerprint(self, normalized_detail: dict) -> str:
        return normalized_detail.get("url", "")


class NewsPortalAdapter(CompanyAnnouncementAdapter):
    source_name = "news_portal"


class SearchAggregatorAdapter(CompanyAnnouncementAdapter):
    source_name = "search_aggregator"