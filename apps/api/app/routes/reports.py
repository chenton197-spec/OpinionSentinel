from __future__ import annotations

from fastapi import APIRouter, status

from app.schemas.domain import ReportCreateRequest, ReportTask
from app.services.report_service import create_report, list_reports

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportTask])
def reports_list() -> list[ReportTask]:
    return list_reports()


@router.post("", response_model=ReportTask, status_code=status.HTTP_201_CREATED)
def reports_create(payload: ReportCreateRequest) -> ReportTask:
    return create_report(payload)
