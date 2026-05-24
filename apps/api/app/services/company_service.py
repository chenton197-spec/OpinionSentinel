from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha1
from html import unescape
import re
from urllib.parse import quote_plus, urlparse
from xml.etree import ElementTree

from bs4 import BeautifulSoup
import httpx

from app.data.demo_store import (
    build_article_id,
    get_articles,
    get_company_profile,
    replace_generated_rules,
    update_company_profile,
    upsert_articles,
)

from app.pipelines.sentiment import heuristic_sentiment, NEGATIVE_HINTS
from app.crawlers.runners import fetch_google_news, fetch_company_announcements, fetch_bing_news, _strip_html

from app.schemas.domain import (
    Article,
    CompanyBootstrapResult,
    CompanyProfile,
    CompanyProfileUpdateRequest,
    KeywordHit,
    KeywordRule,
    SentimentLabel,
    SentimentResult,
    SourceType,
)

OFFICIAL_HINTS = ["官网", "官方", "公告", "声明", "回应", "新闻稿", "investor", "ir", "press", "notice", "announcement"]


def _normalize_terms(items: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        value = item.strip()
        if not value:
            continue
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(value)
    return normalized


def _derived_keywords(company_name: str, aliases: list[str], provided_keywords: list[str], industry: str) -> list[str]:
    import json
    import logging
    from app.core.llm import llm_client
    logger = logging.getLogger(__name__)
    
    base = [company_name, *aliases, *provided_keywords]
    base_default = base + [industry, f"{company_name} 投诉", f"{company_name} 客服", f"{company_name} 售后"]
    
    try:
        prompt = f'请为公司“{company_name}”（行业：{industry}）生成5-8个用于舆情监控的高频搜索关键词组合（如：产品质量、黑猫投诉、股价、裁员等相关词汇结合公司名字），要求返回纯 JSON 字符串数组格式：\n["小米 质量", "小米 维权"]\n不要输出其他任何解释性文字或markdown符号。"'
        msg_content = llm_client.generate_json(prompt, disable_reasoning=True)
        start_idx = msg_content.find("[")
        end_idx = msg_content.rfind("]")
        if start_idx != -1 and end_idx != -1:
            llm_words = json.loads(msg_content[start_idx:end_idx+1])
            base.extend(llm_words)
            return _normalize_terms(base)
    except Exception as exc:
        from fastapi import HTTPException
        if isinstance(exc, HTTPException):
            raise exc
        logger.warning(f"LLM keyword generation failed: {exc}")
    
    return _normalize_terms(base_default)


def _build_generated_rules(profile: CompanyProfile) -> list[KeywordRule]:
    import json
    import logging
    from app.core.llm import llm_client
    logger = logging.getLogger(__name__)
    tz = timezone(timedelta(hours=8))
    
    brand_terms = _normalize_terms([profile.company_name, *profile.aliases])[:5]
    risk_terms = _normalize_terms([profile.company_name, *profile.aliases, *NEGATIVE_HINTS])[:8]
    
    default_rules = [
        KeywordRule(
            id="rule-generated-brand-watch",
            name=f"{profile.company_name} 品牌监控",
            include_keywords=brand_terms,
            exclude_keywords=[],
            sentiment_threshold=None,
            source_scope=[SourceType.COMPANY, SourceType.NEWS, SourceType.SEARCH],
            enabled=True,
            notification_channels=["feishu"],
            created_by="system-generated",
            updated_at=datetime.now(tz=tz),
        ),
        KeywordRule(
            id="rule-generated-negative-watch",
            name=f"{profile.company_name} 负面风险",
            include_keywords=risk_terms,
            exclude_keywords=["招聘", "校招"],
            sentiment_threshold=SentimentLabel.NEGATIVE,
            source_scope=[SourceType.NEWS, SourceType.SEARCH],
            enabled=True,
            notification_channels=["feishu", "email"],
            created_by="system-generated",
            updated_at=datetime.now(tz=tz),
        ),
    ]

    try:
        prompt = (
            f'''请为公司“{profile.company_name}”（行业：{profile.industry}）生成 2 到 3 个用于舆情监控的智能规则设置。\n"
            f"规则需涵盖行业特有风险（例如：如果车企就是电池、刹车、自燃；如果游戏就是版号、外挂、退款等）和特定的高管动态等。\n"
            f"要求返回纯 JSON 数组，格式如下：\n"
            f"[{{\"name\":\"规则名称\", \"include_keywords\":[\"词1\",\"词2\"], \"exclude_keywords\":[], \"sentiment_threshold\":\"negative\"}}]\n"
            f"不要输出其他任何解释性文字或markdown符号。'''
        )
        msg_content = llm_client.generate_json(prompt, disable_reasoning=True)
        start_idx = msg_content.find("[")
        end_idx = msg_content.rfind("]")
        if start_idx != -1 and end_idx != -1:
            rules_data = json.loads(msg_content[start_idx:end_idx+1])
            generated = []
            for i, rd in enumerate(rules_data):
                generated.append(KeywordRule(
                    id=f"rule-generated-llm-{i}",
                    name=f"{profile.company_name} {rd.get('name', '智能监控')}",
                    include_keywords=_normalize_terms(rd.get("include_keywords", [])),
                    exclude_keywords=_normalize_terms(rd.get("exclude_keywords", [])),
                    sentiment_threshold=SentimentLabel(rd.get("sentiment_threshold", "negative").lower()) if rd.get("sentiment_threshold") else None,
                    source_scope=[SourceType.COMPANY, SourceType.NEWS, SourceType.SEARCH],
                    enabled=True,
                    notification_channels=["feishu"],
                    created_by="system-generated",
                    updated_at=datetime.now(tz=tz),
                ))
            if generated:
                return generated
    except Exception as exc:
        from fastapi import HTTPException
        if isinstance(exc, HTTPException):
            raise exc
        logger.warning(f"LLM rules generation failed: {exc}")

    return default_rules








def _source_domain(link: str) -> str:
    return urlparse(link).netloc or "unknown-source"


def _contains_brand_reference(value: str, profile: CompanyProfile) -> bool:
    normalized_value = value.lower()
    terms = [profile.company_name, *profile.aliases]
    return any(term.strip().lower() in normalized_value for term in terms if term.strip())


def _build_article(
    profile: CompanyProfile,
    title: str,
    link: str,
    description: str,
    published_at: datetime,
    source_name: str,
    source_type: SourceType,
    generated_rules: list[KeywordRule] = None,
) -> Article:
    body_text = f"{title} {description}"
    matched_terms = [term for term in profile.keywords if term.lower() in body_text.lower()]
    sentiment_label, confidence, reason, risk_score = heuristic_sentiment(body_text)
    if generated_rules is None:
        generated_rules = _build_generated_rules_fast(profile)
    return Article(
        id=build_article_id("rss", title, link),
        title=title,
        summary=description[:180] or title,
        content=description or title,
        source_name=source_name,
        source_type=source_type,
        source_domain=_source_domain(link),
        original_url=link,
        author=source_name,
        published_at=published_at,
        crawled_at=datetime.now(tz=timezone(timedelta(hours=8))),
        fingerprint=sha1(f"{title}|{link}".encode("utf-8")).hexdigest(),
        sentiment=SentimentResult(
            label=sentiment_label,
            confidence=confidence,
            analyzed_at=datetime.now(tz=timezone(timedelta(hours=8))),
            reason=reason,
        ),
        keyword_hits=[KeywordHit(keyword=term, matched_text=term) for term in matched_terms[:6]],
        tags=[profile.company_name, profile.industry, source_name],
        region=profile.regions[0] if profile.regions else "全国",
        industry=profile.industry,
        rule_hit_ids=[rule.id for rule in generated_rules if any(term in rule.include_keywords for term in matched_terms)],
        risk_score=risk_score,
    )






def _fetch_bing_news(profile: CompanyProfile, limit: int, generated_rules: list[KeywordRule] = None) -> tuple[str, list[Article]]:
    query = quote_plus(profile.company_name)
    url = f"https://www.bing.com/news/search?q={query}"
    response = httpx.get(url, timeout=8.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    articles: list[Article] = []
    seen_links: set[str] = set()

    for tag in soup.find_all("a", href=True):
        title = " ".join(tag.get_text(" ", strip=True).split())
        link = tag.get("href", "").strip()
        if not title or not link.startswith("http") or link in seen_links:
            continue
        if len(title) < 8:
            continue
        seen_links.add(link)
        articles.append(
            _build_article(
                profile,
                title,
                link,
                title,
                datetime.now(tz=timezone(timedelta(hours=8))),
                "Bing News",
                SourceType.SEARCH,
                generated_rules=generated_rules,
            )
        )
        if len(articles) >= limit:
            break

    return "Bing News", articles


def read_company_profile() -> CompanyProfile:
    return get_company_profile()


def _build_generated_rules_fast(profile: CompanyProfile) -> list[KeywordRule]:
    tz = timezone(timedelta(hours=8))
    brand_terms = _normalize_terms([profile.company_name, *profile.aliases])[:5]
    risk_terms = _normalize_terms([profile.company_name, *profile.aliases, *NEGATIVE_HINTS])[:8]
    
    return [
        KeywordRule(
            id="rule-generated-brand-watch",
            name=f"{profile.company_name} 品牌监控",
            include_keywords=brand_terms,
            exclude_keywords=[],
            sentiment_threshold=None,
            source_scope=[SourceType.COMPANY, SourceType.NEWS, SourceType.SEARCH],
            enabled=True,
            notification_channels=["feishu"],
            created_by="system-generated",
            updated_at=datetime.now(tz=tz),
        ),
        KeywordRule(
            id="rule-generated-negative-watch",
            name=f"{profile.company_name} 负面风险",
            include_keywords=risk_terms,
            exclude_keywords=["招聘", "校招"],
            sentiment_threshold=SentimentLabel.NEGATIVE,
            source_scope=[SourceType.NEWS, SourceType.SEARCH],
            enabled=True,
            notification_channels=["feishu", "email"],
            created_by="system-generated",
            updated_at=datetime.now(tz=tz),
        ),
    ]

def save_company_profile_fast(payload: CompanyProfileUpdateRequest) -> CompanyProfile:
    tz = timezone(timedelta(hours=8))
    normalized_aliases = [item.strip() for item in payload.aliases if item.strip()]
    normalized_regions = [item.strip() for item in payload.regions if item.strip()]
    
    base_keywords = [payload.company_name, *normalized_aliases, *[item.strip() for item in payload.keywords if item.strip()]]
    base_default = base_keywords + [payload.industry, f"{payload.company_name} 投诉", f"{payload.company_name} 客服", f"{payload.company_name} 售后"]
    normalized_keywords = _normalize_terms(base_default)

    profile = CompanyProfile(
        company_name=payload.company_name.strip(),
        aliases=normalized_aliases,
        industry=payload.industry.strip(),
        regions=normalized_regions,
        keywords=normalized_keywords,
        notes=payload.notes.strip(),
        updated_at=datetime.now(tz=tz),
    )
    saved = update_company_profile(profile)
    replace_generated_rules(_build_generated_rules_fast(saved))
    return saved


def save_company_profile_llm_background(payload: CompanyProfileUpdateRequest) -> CompanyProfile:
    tz = timezone(timedelta(hours=8))
    normalized_aliases = [item.strip() for item in payload.aliases if item.strip()]
    normalized_regions = [item.strip() for item in payload.regions if item.strip()]
    normalized_keywords = _derived_keywords(
        payload.company_name,
        normalized_aliases,
        [item.strip() for item in payload.keywords if item.strip()],
        payload.industry,
    )

    profile = CompanyProfile(
        company_name=payload.company_name.strip(),
        aliases=normalized_aliases,
        industry=payload.industry.strip(),
        regions=normalized_regions,
        keywords=normalized_keywords,
        notes=payload.notes.strip(),
        updated_at=datetime.now(tz=tz),
    )
    saved = update_company_profile(profile)
    replace_generated_rules(_build_generated_rules(saved))
    return saved


def _llm_filter_important_articles(articles: list[Article], profile: CompanyProfile, limit: int) -> list[Article]:
    import json
    import logging
    from app.core.llm import llm_client
    
    if not articles:
        return []
        
    logger = logging.getLogger(__name__)
    article_summaries = []
    for i, a in enumerate(articles):
        article_summaries.append(f"[{i}] {a.title} - {a.summary[:100]}")
    
    summaries_text = "\n".join(article_summaries)
    prompt = f"""针对公司“{profile.company_name}”的以下过往舆情/新闻报道，请筛选出最重要、最具风险或最具代表性的最多 {limit} 条舆情新闻以供高管回顾。
只需严格返回选中的文章编号，格式必须为纯 JSON 数组（例如 [0, 2, 5]），不要任何 markdown 标记、解释或额外文字。
如果当前没有值得关注的重要舆情，返回 []。
新闻列表：
{summaries_text}
"""
    try:
        msg_content = llm_client.generate_json(prompt, disable_reasoning=True)
        start_idx = msg_content.find("[")
        end_idx = msg_content.rfind("]")
        if start_idx != -1 and end_idx != -1:
            indices = json.loads(msg_content[start_idx:end_idx+1])
            if isinstance(indices, list):
                return [articles[i] for i in indices if 0 <= i < len(articles)]
    except Exception as exc:
        logger.warning(f"LLM filtering failed: {exc}")
        
    return articles[:limit]


def refresh_company_news(limit: int = 8) -> CompanyBootstrapResult:
    profile = get_company_profile()
    generated_rules = _build_generated_rules_fast(profile)
    rule_names = [rule.name for rule in generated_rules]
    source_labels: list[str] = []
    articles: list[Article] = []

    try:
        announcement_label, announcement_articles = fetch_company_announcements(profile, max(2, limit // 2), _build_article, generated_rules=generated_rules)
        if announcement_articles:
            source_labels.append(announcement_label)
            articles.extend(announcement_articles)
    except Exception:
        pass

    try:
        news_label, news_articles = fetch_google_news(profile, max(3, limit - len(articles)), _build_article, generated_rules=generated_rules, time_range="1d")
        if news_articles:
            source_labels.append(news_label)
            articles.extend(news_articles)
    except Exception:
        pass

    try:
        _, historical_articles = fetch_google_news(profile, 50, _build_article, generated_rules=generated_rules, time_range="30d")
        if historical_articles:
            important_historical = _llm_filter_important_articles(historical_articles, profile, limit=3)
            current_fingerprints = {a.fingerprint for a in articles}
            for ha in important_historical:
                if ha.fingerprint not in current_fingerprints:
                    ha.source_name += " (高价值回顾)"
                    articles.append(ha)
                    current_fingerprints.add(ha.fingerprint)
            if important_historical and "新闻门户 (高价值回顾)" not in source_labels:
                source_labels.append("长期重点舆情挖掘")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Historical LLM sub-fetch failed: {e}")

    if not articles:
        try:
            fallback_label, fallback_articles = fetch_bing_news(profile, limit, _build_article, generated_rules=generated_rules)
            source_labels.append(fallback_label)
            articles.extend(fallback_articles)
        except Exception:
            source_labels.append("Google News RSS / Bing unavailable")

    replace_generated_rules(generated_rules)
    inserted_count = upsert_articles(articles)
    total_articles = len(get_articles())
    return CompanyBootstrapResult(
        company_profile=profile,
        generated_rule_names=rule_names,
        fetched_articles=inserted_count,
        total_articles=total_articles,
        source_label=" + ".join(source_labels),
        article_titles=[article.title for article in articles[:5]],
    )

def enrich_company_profile(company_name: str) -> dict[str, object]:
    """Use LLM to enrich company profile based on just the name."""
    import json
    import logging
    from app.core.llm import llm_client
    logger = logging.getLogger(__name__)
    
    default_resp = {
        "aliases": [],
        "industry": "",
        "regions": ["全国"],
        "keywords": [],
        "notes": ""
    }
        
    try:
        prompt = (
            f'''请为公司“{company_name}”补充企业画像，用于舆情监控系统。\n"
            f"请返回纯 JSON 格式：\n"
            f"{{\n"
            f"  \"aliases\": [\"别名1\", \"别名2\"], // 如果没有填空数组\n"
            f"  \"industry\": \"所属行业\", // 例如：互联网 / 游戏 / 消费电子\n"
            f"  \"regions\": [\"全国\", \"出海\"], // 相关地域\n"
            f"  \"keywords\": [\"品牌相关词1\", \"品牌相关词2\"], // 除带公司名的其它搜索词\n"
            f"  \"notes\": \"一段简短的监控重点说明\"\n"
            f"}}\n"
            f"不要输出任何其他说明解释或 markdown 符号。'''
        )
        msg_content = llm_client.generate_json(prompt, disable_reasoning=True)
        start_idx = msg_content.find("{")
        end_idx = msg_content.rfind("}")
        if start_idx != -1 and end_idx != -1:
            data = json.loads(msg_content[start_idx:end_idx+1])
            return {
                "aliases": data.get("aliases", []),
                "industry": data.get("industry", ""),
                "regions": data.get("regions", ["全国"]),
                "keywords": data.get("keywords", []),
                "notes": data.get("notes", "")
            }
    except Exception as exc:
        from fastapi import HTTPException
        if isinstance(exc, HTTPException):
            raise exc
        logger.warning(f"LLM enrich company profile failed: {exc}")
        
    return default_resp
