from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from html import unescape
from typing import Iterable, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

try:
    from dateutil import parser as date_parser
except Exception:  # pragma: no cover
    date_parser = None

TRACKING_PARAM_PREFIXES = (
    "utm_",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "mkt_tok",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_datetime_to_utc(raw: Optional[str]) -> Optional[datetime]:
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None

    if date_parser is not None:
        try:
            dt = date_parser.parse(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    # ISO-only fallback when python-dateutil is unavailable.
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def canonicalize_url(url: str, base_url: Optional[str] = None) -> str:
    absolute = urljoin(base_url, url) if base_url else url
    parsed = urlparse(absolute)

    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()

    # Remove default ports for determinism.
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    kept_query = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lower_key = key.lower()
        if lower_key.startswith(TRACKING_PARAM_PREFIXES):
            continue
        kept_query.append((key, value))

    query = urlencode(kept_query, doseq=True)
    return urlunparse((scheme, netloc, path, "", query, ""))


def article_id_from_canonical(canonical_url: str) -> str:
    digest = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()
    return digest[:24]


def strip_html(value: str, max_len: int = 280) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "..."


def pick_first(values: Iterable[Optional[str]]) -> Optional[str]:
    for value in values:
        if value and value.strip():
            return value.strip()
    return None
