from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.domain import Article, ArticleListResponse, SentimentLabel, SourceType
from app.services.article_service import get_article, list_articles

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ArticleListResponse)
def article_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    keyword: Optional[str] = None,
    source_type: Optional[SourceType] = None,
    sentiment: Optional[SentimentLabel] = None,
    only_rule_hits: bool = False,
    company_scope: bool = False,
) -> ArticleListResponse:
    return list_articles(
        page=page,
        page_size=page_size,
        keyword=keyword,
        source_type=source_type,
        sentiment=sentiment,
        only_rule_hits=only_rule_hits,
        company_scope=company_scope,
    )


@router.get("/{article_id}", response_model=Article)
def article_detail(article_id: str) -> Article:
    try:
        return get_article(article_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Article not found") from exc
