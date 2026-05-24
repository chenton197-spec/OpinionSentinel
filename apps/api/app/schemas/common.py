from enum import Enum

from pydantic import BaseModel


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class SourceType(str, Enum):
    company = "company"
    news = "news"
    search = "search"
    social = "social"


class NotificationStatus(str, Enum):
    pending = "pending"
    delivered = "delivered"
    failed = "failed"


class ReportStatus(str, Enum):
    queued = "queued"
    running = "running"
    ready = "ready"
    failed = "failed"


class ApiMessage(BaseModel):
    message: str
