from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import Sentiment


class KeywordRule(BaseModel):
    id: str
    name: str
    include_keywords: List[str]
    exclude_keywords: List[str]
    sentiment_threshold: Optional[Sentiment] = None
    source_scope: List[str]
    enabled: bool
    notification_channel: str
    created_by: str
    updated_at: str


class KeywordRuleCreate(BaseModel):
    name: str
    include_keywords: List[str]
    exclude_keywords: List[str] = []
    sentiment_threshold: Optional[Sentiment] = None
    source_scope: List[str] = []
    notification_channel: str = "feishu"
