from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import Sentiment, SourceType


class SourceInfo(BaseModel):
    id: str
    name: str
    source_type: SourceType
    homepage: Optional[str] = None


class SentimentResult(BaseModel):
    label: Sentiment
    confidence: float
    summary: str


class Article(BaseModel):
    id: str
    title: str
    summary: str
    content: str
    source_name: str
    source_type: SourceType
    source_url: str
    author: str
    published_at: str
    crawled_at: str
    fingerprint: str
    sentiment: SentimentResult
    keyword_hits: List[str]
    tags: List[str]
    regions: List[str]
    industries: List[str]
    hit_rule: bool = False
    monitoring_status: str


class ArticleListResponse(BaseModel):
    items: List[Article]
    total: int
    page: int
    page_size: int


class ArticleDetailResponse(BaseModel):
    article: Article
    related_articles: List[Article]
