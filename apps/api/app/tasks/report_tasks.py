from __future__ import annotations

from app.services.report_service import generate_report_export
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.report_tasks.generate_report_export")
def generate_report_export_task(report_id: str) -> dict[str, str]:
    report = generate_report_export(report_id)
    return {
        "id": report.id,
        "status": report.status.value,
        "output_format": report.output_format.value,
        "download_url": report.download_url or "",
    }