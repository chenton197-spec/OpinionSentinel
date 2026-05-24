from typing import Optional


ARTICLE_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "summary": {"type": "text"},
            "content": {"type": "text"},
            "source_name": {"type": "keyword"},
            "source_type": {"type": "keyword"},
            "published_at": {"type": "date"},
            "sentiment": {"type": "keyword"},
            "keyword_hits": {"type": "keyword"},
            "tags": {"type": "keyword"},
        }
    }
}


def build_article_query(keyword: Optional[str] = None, sentiment: Optional[str] = None) -> dict[str, object]:
    must: list[dict[str, object]] = []
    if keyword:
        must.append({"multi_match": {"query": keyword, "fields": ["title^3", "summary", "content"]}})
    if sentiment:
        must.append({"term": {"sentiment": sentiment}})
    return {"query": {"bool": {"must": must or [{"match_all": {}}]}}}
