from fastapi import APIRouter

from app.data.demo_data import clone_demo_data
from app.schemas.common import ApiMessage

router = APIRouter(tags=["system"])


@router.get("/health", response_model=ApiMessage)
def healthcheck() -> ApiMessage:
    return ApiMessage(message="ok")


@router.get("/settings")
def get_system_summary() -> dict[str, object]:
    demo_data = clone_demo_data()
    return {
        "mode": "demo",
        "source_count": len(demo_data["sources"]),
        "crawler_jobs": demo_data["crawler_jobs"],
        "integrations": ["FastAPI", "PostgreSQL", "Elasticsearch", "Redis", "Celery", "Feishu/Email"],
    }
