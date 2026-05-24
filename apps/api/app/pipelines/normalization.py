from __future__ import annotations

import hashlib
import re


def clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def normalize_url(url: str) -> str:
    return url.rstrip("/").strip()


def build_fingerprint(title: str, content: str) -> str:
    raw = f"{title}|{content}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()