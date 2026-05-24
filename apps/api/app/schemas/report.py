from pydantic import BaseModel

from app.schemas.common import ReportStatus


class ReportTask(BaseModel):
    id: str
    report_type: str
    time_range: str
    status: ReportStatus
    download_url: str
    triggered_by: str
    created_at: str


class ReportTaskCreate(BaseModel):
    report_type: str
    time_range: str
    triggered_by: str = "system-admin"
