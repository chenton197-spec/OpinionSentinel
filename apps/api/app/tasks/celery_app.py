from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "reputation_monitor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.default_timezone,
    enable_utc=False,
    task_track_started=True,
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
)

celery_app.autodiscover_tasks(["app.tasks"])


def describe_async_flows() -> dict[str, list[str]]:
    return {
        "crawler": ["fetch", "normalize", "deduplicate", "persist"],
        "analysis": ["sentiment", "keyword_match", "alert_dispatch"],
        "report": ["aggregate", "render_html", "export_pdf"],
    }