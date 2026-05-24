from typing import Optional

from pydantic import BaseModel

from app.schemas.common import NotificationStatus


class AlertEvent(BaseModel):
    id: str
    rule_id: str
    article_id: str
    article_title: str
    trigger_reason: str
    triggered_at: str
    notification_status: NotificationStatus
    notification_receipt: Optional[str] = None
