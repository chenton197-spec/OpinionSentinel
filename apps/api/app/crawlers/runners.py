
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import httpx
from app.schemas.domain import Article, CompanyProfile, KeywordRule, SourceType
from app.data.demo_store import build_article_id

def _strip_html(value: str) -> str:
    import re
    from html import unescape
    return re.sub(r"<[^>]+>", "", unescape(value)).strip()

def _build_query(profile: CompanyProfile) -> str:
    brand_terms = [profile.company_name, *profile.aliases][:3]
    if not brand_terms:
        return profile.company_name
    return " OR ".join(f'"{term}"' for term in brand_terms)

def fetch_google_news(profile: CompanyProfile, limit: int, build_article_fn, generated_rules: list = None, time_range: str = None) -> tuple[str, list[Article]]:
    query = _build_query(profile)
    if time_range:
        query += f" when:{time_range}"
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    response = httpx.get(url, timeout=8.0, follow_redirects=True)
    response.raise_for_status()

    root = ElementTree.fromstring(response.text)
    channel = root.find("channel")
    items = channel.findall("item") if channel is not None else []
    articles = []

    for item in items[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = _strip_html(item.findtext("description") or "")
        pub_date_raw = item.findtext("pubDate") or ""
        try:
            published_at = parsedate_to_datetime(pub_date_raw).astimezone(timezone(timedelta(hours=8)))
        except Exception:
            published_at = datetime.now(tz=timezone(timedelta(hours=8)))
        if not title or not link:
            continue
        source_name = (item.findtext("source") or "Google News RSS").strip()
        articles.append(build_article_fn(profile, title, link, description, published_at, source_name, SourceType.NEWS, generated_rules=generated_rules))
    return "Google News RSS / 新闻门户", articles

def fetch_company_announcements(profile: CompanyProfile, limit: int, build_article_fn, generated_rules: list = None) -> tuple[str, list[Article]]:
    query = quote_plus(f'{profile.company_name} 官网 公告 OR 声明 OR 回应')
    url = f"https://www.bing.com/search?q={query}"
    response = httpx.get(url, timeout=8.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for result in soup.select("li.b_algo")[:limit]:
        anchor = result.select_one("h2 a") or result.select_one("a")
        if not anchor: continue
        title = _strip_html(anchor.get_text())
        link = anchor.get("href", "")
        if not link.startswith("http"): continue
        desc = result.select_one("div.b_caption p")
        description = _strip_html(desc.get_text()) if desc else ""
        published_at = datetime.now(tz=timezone(timedelta(hours=8)))
        articles.append(build_article_fn(profile, title, link, description, published_at, "官网/公告", SourceType.COMPANY, generated_rules=generated_rules))
    return "Bing 官网/公告", articles

def fetch_bing_news(profile: CompanyProfile, limit: int, build_article_fn, generated_rules: list = None) -> tuple[str, list[Article]]:
    query = quote_plus(profile.company_name)
    url = f"https://www.bing.com/news/search?q={query}"
    response = httpx.get(url, timeout=8.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for card in soup.select("div.news-card")[:limit]:
        anchor = card.select_one("a.title")
        if not anchor: continue
        title = _strip_html(anchor.get_text())
        link = anchor.get("href", "")
        snippet = card.select_one("div.snippet")
        description = _strip_html(snippet.get_text()) if snippet else ""
        source = card.select_one("div.source a") or card.select_one("div.source")
        source_name = _strip_html(source.get_text()) if source else "Bing News"
        published_at = datetime.now(tz=timezone(timedelta(hours=8)))
        articles.append(build_article_fn(profile, title, link, description, published_at, source_name, SourceType.NEWS, generated_rules=generated_rules))
    return "Bing 新闻搜索", articles
