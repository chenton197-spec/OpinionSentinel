from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha1
from threading import Lock
from typing import Optional
from uuid import uuid4

from sqlalchemy import delete, select

from app.db.session import SessionLocal, engine
from app.models.entities import AlertRecord, ArticleRecord, CompanyProfileRecord, ReportTaskRecord, RuleRecord
from app.schemas.domain import (
    AlertEvent,
    Article,
    CompanyProfile,
    DistributionItem,
    KeywordHit,
    KeywordRule,
    NotificationStatus,
    ReportOutputFormat,
    ReportStatus,
    ReportTask,
    SentimentLabel,
    SentimentResult,
    SourceType,
)

TZ = timezone(timedelta(hours=8))
NOW = datetime(2026, 5, 24, 10, 0, tzinfo=TZ)
DEFAULT_COMPANY_PROFILE_ID = "default"
_INIT_LOCK = Lock()
_INITIALIZED = False


def _sentiment(label: SentimentLabel, confidence: float, reason: str, hours_ago: int) -> SentimentResult:
    return SentimentResult(
        label=label,
        confidence=confidence,
        analyzed_at=NOW - timedelta(hours=hours_ago),
        reason=reason,
    )


SEED_ARTICLES: list[Article] = []

SEED_RULES: list[KeywordRule] = [
    KeywordRule(
        id="rule-001",
        name="高风险品牌投诉",
        include_keywords=["物流", "客服", "投诉"],
        exclude_keywords=["招聘"],
        sentiment_threshold=SentimentLabel.NEGATIVE,
        source_scope=[SourceType.NEWS, SourceType.SEARCH],
        enabled=True,
        notification_channels=["feishu"],
        created_by="ops_lead",
        updated_at=NOW - timedelta(hours=12),
    ),
    KeywordRule(
        id="rule-002",
        name="官网公告跟踪",
        include_keywords=["公告", "回应", "说明"],
        exclude_keywords=[],
        sentiment_threshold=None,
        source_scope=[SourceType.COMPANY],
        enabled=True,
        notification_channels=["email"],
        created_by="brand_manager",
        updated_at=NOW - timedelta(days=1),
    ),
    KeywordRule(
        id="rule-003",
        name="负面舆情升级",
        include_keywords=["延迟", "维权", "负面"],
        exclude_keywords=[],
        sentiment_threshold=SentimentLabel.NEGATIVE,
        source_scope=[SourceType.COMPANY, SourceType.NEWS, SourceType.SEARCH],
        enabled=True,
        notification_channels=["feishu", "email"],
        created_by="risk_owner",
        updated_at=NOW - timedelta(hours=5),
    ),
]

SEED_ALERTS: list[AlertEvent] = []

SEED_REPORTS: list[ReportTask] = []

SEED_COMPANY_PROFILE = CompanyProfile(
    company_name="示例品牌",
    aliases=["示例科技", "Example Brand"],
    industry="消费电子",
    regions=["全国", "华东", "华南"],
    keywords=["示例品牌", "售后", "物流", "客服", "新品"],
    notes="当前为演示主体。保存后会同步更新前端展示的监控公司信息，但不会自动替换已有种子舆情内容。",
    updated_at=NOW,
)


def _article_record_from_model(article: Article) -> ArticleRecord:
    return ArticleRecord(
        id=article.id,
        title=article.title,
        summary=article.summary,
        content=article.content,
        source_name=article.source_name,
        source_type=article.source_type.value,
        source_domain=article.source_domain,
        original_url=article.original_url,
        author=article.author,
        published_at=article.published_at,
        crawled_at=article.crawled_at,
        fingerprint=article.fingerprint,
        sentiment_label=article.sentiment.label.value,
        sentiment_confidence=article.sentiment.confidence,
        sentiment_analyzed_at=article.sentiment.analyzed_at,
        sentiment_reason=article.sentiment.reason,
        keyword_hits=[hit.model_dump(mode="json") for hit in article.keyword_hits],
        tags=list(article.tags),
        region=article.region,
        industry=article.industry,
        rule_hit_ids=list(article.rule_hit_ids),
        risk_score=article.risk_score,
    )


def _article_from_record(record: ArticleRecord) -> Article:
    return Article(
        id=record.id,
        title=record.title,
        summary=record.summary,
        content=record.content,
        source_name=record.source_name,
        source_type=SourceType(record.source_type),
        source_domain=record.source_domain,
        original_url=record.original_url,
        author=record.author,
        published_at=record.published_at,
        crawled_at=record.crawled_at,
        fingerprint=record.fingerprint,
        sentiment=SentimentResult(
            label=SentimentLabel(record.sentiment_label),
            confidence=record.sentiment_confidence,
            analyzed_at=record.sentiment_analyzed_at,
            reason=record.sentiment_reason,
        ),
        keyword_hits=[KeywordHit(**item) for item in (record.keyword_hits or [])],
        tags=list(record.tags or []),
        region=record.region,
        industry=record.industry,
        rule_hit_ids=list(record.rule_hit_ids or []),
        risk_score=record.risk_score,
    )


def _rule_record_from_model(rule: KeywordRule) -> RuleRecord:
    return RuleRecord(
        id=rule.id,
        name=rule.name,
        include_keywords=list(rule.include_keywords),
        exclude_keywords=list(rule.exclude_keywords),
        sentiment_threshold=rule.sentiment_threshold.value if rule.sentiment_threshold else None,
        source_scope=[source.value for source in rule.source_scope],
        enabled=rule.enabled,
        notification_channels=list(rule.notification_channels),
        created_by=rule.created_by,
        updated_at=rule.updated_at,
    )


def _rule_from_record(record: RuleRecord) -> KeywordRule:
    return KeywordRule(
        id=record.id,
        name=record.name,
        include_keywords=list(record.include_keywords or []),
        exclude_keywords=list(record.exclude_keywords or []),
        sentiment_threshold=SentimentLabel(record.sentiment_threshold) if record.sentiment_threshold else None,
        source_scope=[SourceType(source) for source in (record.source_scope or [])],
        enabled=record.enabled,
        notification_channels=list(record.notification_channels or []),
        created_by=record.created_by,
        updated_at=record.updated_at,
    )


def _alert_record_from_model(alert: AlertEvent) -> AlertRecord:
    return AlertRecord(
        id=alert.id,
        rule_id=alert.rule_id,
        article_id=alert.article_id,
        rule_name=alert.rule_name,
        article_title=alert.article_title,
        trigger_reason=alert.trigger_reason,
        triggered_at=alert.triggered_at,
        notification_status=alert.notification_status.value,
        notification_receipt=alert.notification_receipt,
    )


def _alert_from_record(record: AlertRecord) -> AlertEvent:
    return AlertEvent(
        id=record.id,
        rule_id=record.rule_id,
        article_id=record.article_id,
        rule_name=record.rule_name,
        article_title=record.article_title,
        trigger_reason=record.trigger_reason,
        triggered_at=record.triggered_at,
        notification_status=NotificationStatus(record.notification_status),
        notification_receipt=record.notification_receipt,
    )


def _report_record_from_model(report: ReportTask) -> ReportTaskRecord:
    return ReportTaskRecord(
        id=report.id,
        report_type=report.report_type,
        time_range=report.time_range,
        status=report.status.value,
        output_format=report.output_format.value,
        download_url=report.download_url,
        error_message=report.error_message,
        triggered_by=report.triggered_by,
        created_at=report.created_at,
    )


def _report_from_record(record: ReportTaskRecord) -> ReportTask:
    return ReportTask(
        id=record.id,
        report_type=record.report_type,
        time_range=record.time_range,
        status=ReportStatus(record.status),
        output_format=ReportOutputFormat(record.output_format),
        download_url=record.download_url,
        error_message=record.error_message,
        triggered_by=record.triggered_by,
        created_at=record.created_at,
    )


def _profile_from_record(record: CompanyProfileRecord) -> CompanyProfile:
    return CompanyProfile(
        company_name=record.company_name,
        aliases=list(record.aliases or []),
        industry=record.industry,
        regions=list(record.regions or []),
        keywords=list(record.keywords or []),
        notes=record.notes,
        updated_at=record.updated_at,
    )


def _initialize_database() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return
    with _INIT_LOCK:
        if _INITIALIZED:
            return
        from app.db.session import Base

        Base.metadata.create_all(bind=engine)
        with SessionLocal() as session:
            if session.scalar(select(CompanyProfileRecord.id).limit(1)) is None:
                session.add(
                    CompanyProfileRecord(
                        id=DEFAULT_COMPANY_PROFILE_ID,
                        company_name=SEED_COMPANY_PROFILE.company_name,
                        aliases=list(SEED_COMPANY_PROFILE.aliases),
                        industry=SEED_COMPANY_PROFILE.industry,
                        regions=list(SEED_COMPANY_PROFILE.regions),
                        keywords=list(SEED_COMPANY_PROFILE.keywords),
                        notes=SEED_COMPANY_PROFILE.notes,
                        updated_at=SEED_COMPANY_PROFILE.updated_at,
                    )
                )
            if session.scalar(select(ArticleRecord.id).limit(1)) is None:
                session.add_all([_article_record_from_model(article) for article in SEED_ARTICLES])
            if session.scalar(select(RuleRecord.id).limit(1)) is None:
                session.add_all([_rule_record_from_model(rule) for rule in SEED_RULES])
            if session.scalar(select(AlertRecord.id).limit(1)) is None:
                session.add_all([_alert_record_from_model(alert) for alert in SEED_ALERTS])
            if session.scalar(select(ReportTaskRecord.id).limit(1)) is None:
                session.add_all([_report_record_from_model(report) for report in SEED_REPORTS])
            session.commit()
        _INITIALIZED = True


def initialize_database() -> None:
    _initialize_database()


def get_articles() -> list[Article]:
    _initialize_database()
    with SessionLocal() as session:
        records = session.scalars(select(ArticleRecord).order_by(ArticleRecord.published_at.desc())).all()
        return [_article_from_record(record) for record in records]


def upsert_articles(articles: list[Article]) -> int:
    _initialize_database()
    if not articles:
        return 0
    with SessionLocal() as session:
        known_keys = {
            (original_url, fingerprint)
            for original_url, fingerprint in session.execute(select(ArticleRecord.original_url, ArticleRecord.fingerprint)).all()
        }
        inserted = 0
        for article in articles:
            unique_key = (article.original_url, article.fingerprint)
            if unique_key in known_keys:
                continue
            session.add(_article_record_from_model(article))
            known_keys.add(unique_key)
            inserted += 1
        session.commit()
        return inserted


def get_rules() -> list[KeywordRule]:
    _initialize_database()
    with SessionLocal() as session:
        records = session.scalars(select(RuleRecord).order_by(RuleRecord.updated_at.desc())).all()
        return [_rule_from_record(record) for record in records]


def get_rule(rule_id: str) -> KeywordRule:
    _initialize_database()
    with SessionLocal() as session:
        record = session.get(RuleRecord, rule_id)
        if record is None:
            raise KeyError(rule_id)
        return _rule_from_record(record)


def add_rule(rule: KeywordRule) -> KeywordRule:
    _initialize_database()
    with SessionLocal() as session:
        record = _rule_record_from_model(rule)
        session.add(record)
        session.commit()
        return _rule_from_record(record)


def update_rule(rule: KeywordRule) -> KeywordRule:
    _initialize_database()
    with SessionLocal() as session:
        record = session.get(RuleRecord, rule.id)
        if record is None:
            raise KeyError(rule.id)
        record.name = rule.name
        record.include_keywords = list(rule.include_keywords)
        record.exclude_keywords = list(rule.exclude_keywords)
        record.sentiment_threshold = rule.sentiment_threshold.value if rule.sentiment_threshold else None
        record.source_scope = [source.value for source in rule.source_scope]
        record.enabled = rule.enabled
        record.notification_channels = list(rule.notification_channels)
        record.created_by = rule.created_by
        record.updated_at = rule.updated_at
        session.commit()
        session.refresh(record)
        return _rule_from_record(record)


def delete_rule(rule_id: str) -> None:
    _initialize_database()
    with SessionLocal() as session:
        record = session.get(RuleRecord, rule_id)
        if record is None:
            raise KeyError(rule_id)
        session.delete(record)
        session.commit()


def replace_generated_rules(rules: list[KeywordRule]) -> list[KeywordRule]:
    _initialize_database()
    with SessionLocal() as session:
        session.execute(delete(RuleRecord).where(RuleRecord.created_by == "system-generated"))
        session.add_all([_rule_record_from_model(rule) for rule in rules])
        session.commit()
        return deepcopy(rules)


def get_alerts() -> list[AlertEvent]:
    _initialize_database()
    with SessionLocal() as session:
        records = session.scalars(select(AlertRecord).order_by(AlertRecord.triggered_at.desc())).all()
        return [_alert_from_record(record) for record in records]


def get_reports() -> list[ReportTask]:
    _initialize_database()
    with SessionLocal() as session:
        records = session.scalars(select(ReportTaskRecord).order_by(ReportTaskRecord.created_at.desc())).all()
        return [_report_from_record(record) for record in records]


def get_report(report_id: str) -> ReportTask:
    _initialize_database()
    with SessionLocal() as session:
        record = session.get(ReportTaskRecord, report_id)
        if record is None:
            raise KeyError(report_id)
        return _report_from_record(record)


def add_report(
    report_type: str,
    time_range: str,
    triggered_by: str,
    *,
    output_format: ReportOutputFormat = ReportOutputFormat.HTML,
    status: ReportStatus = ReportStatus.PENDING,
    download_url: Optional[str] = None,
    created_at: Optional[datetime] = None,
    error_message: Optional[str] = None,
) -> ReportTask:
    _initialize_database()
    report = ReportTask(
        id=f"report-{uuid4().hex[:8]}",
        report_type=report_type,
        time_range=time_range,
        status=status,
        output_format=output_format,
        download_url=download_url,
        error_message=error_message,
        triggered_by=triggered_by,
        created_at=created_at or datetime.now(tz=TZ),
    )
    with SessionLocal() as session:
        record = _report_record_from_model(report)
        session.add(record)
        session.commit()
        return _report_from_record(record)


def update_report(
    report_id: str,
    *,
    status: Optional[ReportStatus] = None,
    download_url: Optional[str] = None,
    error_message: Optional[str] = None,
) -> ReportTask:
    _initialize_database()
    with SessionLocal() as session:
        record = session.get(ReportTaskRecord, report_id)
        if record is None:
            raise KeyError(report_id)
        if status is not None:
            record.status = status.value
        if download_url is not None:
            record.download_url = download_url
        if error_message is not None:
            record.error_message = error_message
        session.commit()
        session.refresh(record)
        return _report_from_record(record)


def get_company_profile() -> CompanyProfile:
    _initialize_database()
    with SessionLocal() as session:
        record = session.get(CompanyProfileRecord, DEFAULT_COMPANY_PROFILE_ID)
        if record is None:
            raise KeyError(DEFAULT_COMPANY_PROFILE_ID)
        return _profile_from_record(record)


def update_company_profile(profile: CompanyProfile) -> CompanyProfile:
    _initialize_database()
    with SessionLocal() as session:
        record = session.get(CompanyProfileRecord, DEFAULT_COMPANY_PROFILE_ID)
        if record is None:
            record = CompanyProfileRecord(id=DEFAULT_COMPANY_PROFILE_ID)
            session.add(record)
        record.company_name = profile.company_name
        record.aliases = list(profile.aliases)
        record.industry = profile.industry
        record.regions = list(profile.regions)
        record.keywords = list(profile.keywords)
        record.notes = profile.notes
        record.updated_at = profile.updated_at
        session.commit()
        session.refresh(record)
        return _profile_from_record(record)


def keyword_frequency() -> list[DistributionItem]:
    counter: dict[str, int] = {}
    for article in get_articles():
        for hit in article.keyword_hits:
            counter[hit.keyword] = counter.get(hit.keyword, 0) + 1
    return [DistributionItem(label=key, value=value) for key, value in sorted(counter.items(), key=lambda item: item[1], reverse=True)]


def build_article_id(prefix: str, title: str, url: str) -> str:
    digest = sha1(f"{title}|{url}".encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"