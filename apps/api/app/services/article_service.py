from __future__ import annotations

from typing import Optional

from app.data.demo_store import get_articles, get_company_profile
from app.schemas.domain import Article, ArticleListResponse, SentimentLabel, SourceType


def _company_scope_terms() -> list[str]:
    profile = get_company_profile()
    brand_terms = [profile.company_name, *profile.aliases]
    normalized_brand_terms = [term.strip().lower() for term in brand_terms if term.strip()]
    scoped_terms = [term.strip() for term in brand_terms if term.strip()]

    for keyword in profile.keywords:
        value = keyword.strip()
        lowered = value.lower()
        if not value:
            continue
        if any(brand_term in lowered for brand_term in normalized_brand_terms):
            scoped_terms.append(value)

    seen: set[str] = set()
    result: list[str] = []
    for term in scoped_terms:
        lowered = term.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(term)
    return result


def _matches_company_scope(article: Article) -> bool:
    terms = _company_scope_terms()
    haystacks = [
        article.title,
        article.summary,
        article.content,
        article.source_name,
        " ".join(article.tags),
        " ".join(hit.keyword for hit in article.keyword_hits),
    ]
    for term in terms:
        lowered = term.strip().lower()
        if not lowered:
            continue
        if any(lowered in haystack.lower() for haystack in haystacks):
            return True
    return False


def list_articles(
    *,
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    source_type: Optional[SourceType] = None,
    sentiment: Optional[SentimentLabel] = None,
    only_rule_hits: bool = False,
    company_scope: bool = False,
) -> ArticleListResponse:
    items = get_articles()

    if company_scope:
        items = [article for article in items if _matches_company_scope(article)]

    if keyword:
        normalized = keyword.lower()
        items = [
            article
            for article in items
            if normalized in article.title.lower()
            or normalized in article.summary.lower()
            or any(normalized in hit.keyword.lower() for hit in article.keyword_hits)
        ]

    if source_type:
        items = [article for article in items if article.source_type == source_type]

    if sentiment:
        items = [article for article in items if article.sentiment.label == sentiment]

    if only_rule_hits:
        items = [article for article in items if article.rule_hit_ids]

    items.sort(key=lambda article: article.published_at, reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return ArticleListResponse(items=items[start:end], total=total, page=page, page_size=page_size)


def get_article(article_id: str) -> Article:
    for article in get_articles():
        if article.id == article_id:
            return article
    raise KeyError(article_id)
