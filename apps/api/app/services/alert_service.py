from __future__ import annotations

from app.data.demo_store import get_alerts
from app.schemas.domain import AlertEvent


def list_alerts() -> list[AlertEvent]:
    alerts = get_alerts()
    alerts.sort(key=lambda item: item.triggered_at, reverse=True)
    return alerts
