from __future__ import annotations

from typing import Optional


def build_article_query(*, keyword: Optional[str], source_type: Optional[str], sentiment: Optional[str]) -> dict:
    must: list[dict] = []
    if keyword:
        must.append({"multi_match": {"query": keyword, "fields": ["title^3", "summary", "content"]}})
    if source_type:
        must.append({"term": {"source_type.keyword": source_type}})
    if sentiment:
        must.append({"term": {"sentiment.label.keyword": sentiment}})
    return {"query": {"bool": {"must": must or [{"match_all": {}}]}}}