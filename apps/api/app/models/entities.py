from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ArticleRecord(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("original_url", "fingerprint", name="uq_articles_url_fingerprint"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    original_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    sentiment_label: Mapped[str] = mapped_column(String(32), nullable=False)
    sentiment_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sentiment_reason: Mapped[str] = mapped_column(Text, nullable=False)
    keyword_hits: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    region: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_hit_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)


class RuleRecord(Base):
    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    include_keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    exclude_keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    sentiment_threshold: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source_scope: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_channels: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AlertRecord(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    article_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    article_title: Mapped[str] = mapped_column(String(512), nullable=False)
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notification_status: Mapped[str] = mapped_column(String(32), nullable=False)
    notification_receipt: Mapped[str] = mapped_column(Text, nullable=False)


class ReportTaskRecord(Base):
    __tablename__ = "report_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    report_type: Mapped[str] = mapped_column(String(64), nullable=False)
    time_range: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    output_format: Mapped[str] = mapped_column(String(16), nullable=False, default="html")
    download_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CompanyProfileRecord(Base):
    __tablename__ = "company_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default="default")
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    regions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)