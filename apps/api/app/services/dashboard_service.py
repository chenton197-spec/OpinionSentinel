from __future__ import annotations

from collections import Counter, defaultdict

from app.services.article_service import _matches_company_scope
from app.data.demo_store import get_articles, get_rules, keyword_frequency
from app.schemas.domain import DashboardStats, DistributionItem, SentimentLabel, TrendPoint


def get_dashboard_stats() -> DashboardStats:
    articles = [a for a in get_articles() if _matches_company_scope(a)]
    rules = get_rules()
    if not articles:
        return DashboardStats(
            total_articles=0, negative_ratio=0.0, today_new=0, active_rules=len([r for r in rules if r.enabled]),
            top_source="-", trend=[], source_distribution=[], sentiment_distribution=[], top_keywords=[], highlighted_articles=[]
        )
    news_first_articles = [article for article in articles if article.source_type.value != "search_aggregator"]
    total_articles = len(articles)
    negative_count = len([article for article in articles if article.sentiment.label == SentimentLabel.NEGATIVE])
    today_anchor = max(item.published_at.date() for item in articles)
    today_new = len([article for article in articles if article.published_at.date() == today_anchor])
    source_counter = Counter(article.source_name for article in news_first_articles)
    sentiment_counter = Counter(article.sentiment.label.value for article in articles)
    trend_counter: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "negative": 0})

    for article in articles:
        day = article.published_at.strftime("%m-%d")
        trend_counter[day]["total"] += 1
        if article.sentiment.label == SentimentLabel.NEGATIVE:
            trend_counter[day]["negative"] += 1

    trend = [
        TrendPoint(date=day, total=values["total"], negative=values["negative"])
        for day, values in sorted(trend_counter.items())
    ]

    return DashboardStats(
        total_articles=total_articles,
        negative_ratio=round(negative_count / total_articles, 2) if total_articles else 0,
        today_new=today_new,
        active_rules=len([rule for rule in rules if rule.enabled]),
        top_source=source_counter.most_common(1)[0][0] if source_counter else "-",
        trend=trend,
        source_distribution=[DistributionItem(label=label, value=value) for label, value in source_counter.most_common()],
        sentiment_distribution=[DistributionItem(label=label, value=value) for label, value in sentiment_counter.most_common()],
        top_keywords=keyword_frequency(),
        highlighted_articles=sorted(news_first_articles, key=lambda article: article.risk_score, reverse=True)[:3],
    )
