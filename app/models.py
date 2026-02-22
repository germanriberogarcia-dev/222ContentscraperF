from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class SourceConfig:
    id: str
    name: str
    base_url: str
    feed_url: Optional[str]
    listing_url: str
    scraper_enabled: bool = True
    active: bool = True
    article_selector: str = "article"
    link_selector: str = "h2 a, h3 a, a[href]"
    time_selector: str = "time"
    snippet_selector: str = "p"
    image_selector: str = "img"


@dataclass(frozen=True)
class RawArticle:
    source_id: str
    title: str
    url: str
    published_at_utc: Optional[datetime]
    snippet: str = ""
    image_url: Optional[str] = None


@dataclass(frozen=True)
class NormalizedArticle:
    id: str
    source_id: str
    title: str
    url: str
    canonical_url: str
    published_at_utc: str
    snippet: str
    image_url: Optional[str]
    first_seen_at_utc: str
    last_seen_at_utc: str


@dataclass(frozen=True)
class SourceHealth:
    source_id: str
    source_name: str
    status: str
    checked_at_utc: str
    detail: str
