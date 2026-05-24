import re
from hashlib import sha1


def strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


def normalize_url(url: str) -> str:
    return url.rstrip("/").lower()


def build_fingerprint(title: str, content: str) -> str:
    normalized = f"{title.strip().lower()}::{content.strip().lower()}"
    return sha1(normalized.encode("utf-8")).hexdigest()
