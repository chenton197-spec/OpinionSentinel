from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Company Reputation Monitor API")
    app_env: str = os.getenv("APP_ENV", "development")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/reputation_monitor",
    )
    api_cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("API_CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    )
    default_timezone: str = os.getenv("DEFAULT_TIMEZONE", "Asia/Shanghai")
    default_brand_keywords: tuple[str, ...] = tuple(
        keyword.strip()
        for keyword in os.getenv("DEFAULT_BRAND_KEYWORDS", "公司,品牌,产品").split(",")
        if keyword.strip()
    )
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    celery_task_always_eager: bool = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
    notification_channel: str = os.getenv("NOTIFICATION_CHANNEL", "feishu")
    report_output_dir: str = os.getenv("REPORT_OUTPUT_DIR", "./app/data/exports")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Unified LLM configurations
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
