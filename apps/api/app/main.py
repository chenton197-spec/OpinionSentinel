from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.data.demo_store import initialize_database
from app.routes import alerts, articles, company, dashboard, reports, rules
from app.schemas.domain import HealthCheck

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="MVP API for company sentiment monitoring with demo-ready seed data.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.api_cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(company.router, prefix="/api")
app.include_router(rules.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.on_event("startup")
def app_startup() -> None:
    initialize_database()


@app.get("/health", response_model=HealthCheck)
def health_check() -> HealthCheck:
    if settings.database_url.startswith("postgresql"):
        data_mode = "postgres"
    elif settings.database_url.startswith("sqlite"):
        data_mode = "sqlite"
    else:
        data_mode = "unknown"

    return HealthCheck(
        status="ok",
        app_env=settings.app_env,
        timezone=settings.default_timezone,
        data_mode=data_mode,
    )