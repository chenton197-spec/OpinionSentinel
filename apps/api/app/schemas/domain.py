from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    COMPANY = "company_announcement"
    NEWS = "news_portal"
    SEARCH = "search_aggregator"
    RESERVED = "reserved_extension"


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    PENDING = "pending"
    FAILED = "failed"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ReportStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"


class ReportOutputFormat(str, Enum):
    HTML = "html"
    PDF = "pdf"


class Source(BaseModel):
    id: str
    name: str
    type: SourceType
    domain: str
    enabled: bool = True


class SentimentResult(BaseModel):
    label: SentimentLabel
    confidence: float = Field(ge=0, le=1)
    analyzed_at: datetime
    reason: str


class KeywordHit(BaseModel):
    keyword: str
    matched_text: str


class Article(BaseModel):
    id: str
    title: str
    summary: str
    content: str
    source_name: str
    source_type: SourceType
    source_domain: str
    original_url: str
    author: str
    published_at: datetime
    crawled_at: datetime
    fingerprint: str
    sentiment: SentimentResult
    keyword_hits: list[KeywordHit]
    tags: list[str]
    region: str
    industry: str
    rule_hit_ids: list[str]
    risk_score: int = Field(ge=0, le=100)


class ArticleListResponse(BaseModel):
    items: list[Article]
    total: int
    page: int
    page_size: int


class TrendPoint(BaseModel):
    date: str
    total: int
    negative: int


class DistributionItem(BaseModel):
    label: str
    value: int


class DashboardStats(BaseModel):
    total_articles: int
    negative_ratio: float
    today_new: int
    active_rules: int
    top_source: str
    trend: list[TrendPoint]
    source_distribution: list[DistributionItem]
    sentiment_distribution: list[DistributionItem]
    top_keywords: list[DistributionItem]
    highlighted_articles: list[Article]


class KeywordRule(BaseModel):
    id: str
    name: str
    include_keywords: list[str]
    exclude_keywords: list[str]
    sentiment_threshold: Optional[SentimentLabel] = None
    source_scope: list[SourceType]
    enabled: bool = True
    notification_channels: list[str]
    created_by: str
    updated_at: datetime


class RuleCreateRequest(BaseModel):
    name: str
    include_keywords: list[str]
    exclude_keywords: list[str] = []
    sentiment_threshold: Optional[SentimentLabel] = None
    source_scope: list[SourceType] = [SourceType.COMPANY, SourceType.NEWS, SourceType.SEARCH]
    enabled: bool = True
    notification_channels: list[str] = ["feishu"]
    created_by: str = "demo_admin"


class RuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    include_keywords: Optional[list[str]] = None
    exclude_keywords: Optional[list[str]] = None
    sentiment_threshold: Optional[SentimentLabel] = None
    source_scope: Optional[list[SourceType]] = None
    enabled: Optional[bool] = None
    notification_channels: Optional[list[str]] = None
    created_by: Optional[str] = None


class AlertEvent(BaseModel):
    id: str
    rule_id: str
    article_id: str
    rule_name: str
    article_title: str
    trigger_reason: str
    triggered_at: datetime
    notification_status: NotificationStatus
    notification_receipt: str


class ReportTask(BaseModel):
    id: str
    report_type: str
    time_range: str
    status: ReportStatus
    output_format: ReportOutputFormat = ReportOutputFormat.HTML
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    triggered_by: str
    created_at: datetime


class ReportCreateRequest(BaseModel):
    report_type: str
    time_range: str
    output_format: ReportOutputFormat = ReportOutputFormat.HTML
    triggered_by: str = "demo_admin"


class HealthCheck(BaseModel):
    status: str
    app_env: str
    timezone: str
    data_mode: str


class CompanyProfile(BaseModel):
    company_name: str
    aliases: list[str]
    industry: str
    regions: list[str]
    keywords: list[str]
    notes: str = ""
    updated_at: datetime


class CompanyProfileUpdateRequest(BaseModel):
    company_name: str
    aliases: list[str] = []
    industry: str
    regions: list[str] = []
    keywords: list[str] = []
    notes: str = ""


class CompanyBootstrapResult(BaseModel):
    company_profile: CompanyProfile
    generated_rule_names: list[str]
    fetched_articles: int
    total_articles: int
    source_label: str
    article_titles: list[str]
