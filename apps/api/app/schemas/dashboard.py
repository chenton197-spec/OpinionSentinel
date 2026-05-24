from typing import List

from pydantic import BaseModel


class MetricCard(BaseModel):
    label: str
    value: str
    change: str
    tone: str


class TrendPoint(BaseModel):
    date: str
    total: int
    negative: int


class DistributionItem(BaseModel):
    label: str
    value: int
    percentage: float


class DashboardOverview(BaseModel):
    metrics: List[MetricCard]
    trend: List[TrendPoint]
    source_distribution: List[DistributionItem]
    sentiment_distribution: List[DistributionItem]
    top_keywords: List[DistributionItem]
    focus_articles: List[str]
