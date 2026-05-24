from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.data.demo_store import add_rule, delete_rule, get_rule, get_rules, update_rule
from app.schemas.domain import KeywordRule, RuleCreateRequest, RuleUpdateRequest


def list_rules() -> list[KeywordRule]:
    rules = get_rules()
    rules.sort(key=lambda item: item.updated_at, reverse=True)
    return rules


def create_rule(payload: RuleCreateRequest) -> KeywordRule:
    tz = timezone(timedelta(hours=8))
    rule = KeywordRule(
        id=f"rule-{uuid4().hex[:8]}",
        name=payload.name,
        include_keywords=payload.include_keywords,
        exclude_keywords=payload.exclude_keywords,
        sentiment_threshold=payload.sentiment_threshold,
        source_scope=payload.source_scope,
        enabled=payload.enabled,
        notification_channels=payload.notification_channels,
        created_by=payload.created_by,
        updated_at=datetime.now(tz=tz),
    )
    return add_rule(rule)


def get_rule_detail(rule_id: str) -> KeywordRule:
    return get_rule(rule_id)


def update_rule_detail(rule_id: str, payload: RuleUpdateRequest) -> KeywordRule:
    current = get_rule(rule_id)
    tz = timezone(timedelta(hours=8))
    updated = KeywordRule(
        id=current.id,
        name=payload.name if payload.name is not None else current.name,
        include_keywords=payload.include_keywords if payload.include_keywords is not None else current.include_keywords,
        exclude_keywords=payload.exclude_keywords if payload.exclude_keywords is not None else current.exclude_keywords,
        sentiment_threshold=payload.sentiment_threshold if payload.sentiment_threshold is not None else current.sentiment_threshold,
        source_scope=payload.source_scope if payload.source_scope is not None else current.source_scope,
        enabled=payload.enabled if payload.enabled is not None else current.enabled,
        notification_channels=payload.notification_channels if payload.notification_channels is not None else current.notification_channels,
        created_by=payload.created_by if payload.created_by is not None else current.created_by,
        updated_at=datetime.now(tz=tz),
    )
    return update_rule(updated)


def delete_rule_detail(rule_id: str) -> None:
    delete_rule(rule_id)
