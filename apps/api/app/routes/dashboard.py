from __future__ import annotations

from fastapi import APIRouter

from app.schemas.domain import DashboardStats
from app.services.dashboard_service import get_dashboard_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardStats)
def dashboard_overview() -> DashboardStats:
    return get_dashboard_stats()
