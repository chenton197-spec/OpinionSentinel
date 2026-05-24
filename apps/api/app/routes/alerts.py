from __future__ import annotations

from fastapi import APIRouter

from app.schemas.domain import AlertEvent
from app.services.alert_service import list_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertEvent])
def alerts_list() -> list[AlertEvent]:
    return list_alerts()
