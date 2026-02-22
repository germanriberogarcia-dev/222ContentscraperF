from __future__ import annotations

from datetime import datetime
from typing import Optional
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from app.config import Settings
from app.models import RawArticle, SourceConfig, SourceHealth
from app.utils import canonicalize_url, parse_datetime_to_utc, pick_first, strip_html, to_iso_utc, utc_now


class BaseSourceAdapter:
    def __init__(self, source_config: SourceConfig):
        self.source = source_config

    def fetch(self, settings: Settings) -> tuple[list[RawArticle], list[str]]:
        warnings: list[str] = []

        feed_articles: list[RawArticle] = []
        if self.source.feed_url:
            try:
                feed_articles = self._fetch_from_feed(settings)
            except Exception as exc:
                warnings.append(f"feed_error: {exc}")

        if feed_articles:
            return feed_articles, warnings

        if self.source.scraper_enabled:
            try:
                scraped = self._fetch_from_listing(settings)
                return scraped, warnings
            except Exception as exc:
                warnings.append(f"scrape_error: {exc}")

        return [], warnings

    def check_health(self, settings: Settings) -> SourceHealth:
        checked_at = to_iso_utc(utc_now())

        if self.source.feed_url:
            try:
                text = self._request_text(self.source.feed_url, settings)
                if text.strip():
                    return SourceHealth(
                        source_id=self.source.id,
                        source_name=self.source.name,
                        status="ok",
                        checked_at_utc=checked_at,
                        detail="feed reachable",
                    )
            except Exception as exc:
                feed_error = str(exc)
            else:
                feed_error = "empty feed response"
        else:
            feed_error = "feed not configured"

        try:
            html = self._request_text(self.source.listing_url, settings)
            if html.strip():
                return SourceHealth(
                    source_id=self.source.id,
                    source_name=self.source.name,
                    status="ok",
                    checked_at_utc=checked_at,
                    detail="listing reachable (fallback)",
                )
        except Exception as exc:
            return SourceHealth(
                source_id=self.source.id,
                source_name=self.source.name,
                status="error",
                checked_at_utc=checked_at,
                detail=f"feed/listing unavailable: feed={feed_error}; listing={exc}",
            )

        return SourceHealth(
            source_id=self.source.id,
            source_name=self.source.name,
            status="error",
            checked_at_utc=checked_at,
            detail=f"feed/listing unavailable: feed={feed_error}; listing=empty",
        )

    def _fetch_from_feed(self, settings: Settings) -> list[RawArticle]:
        if not self.source.feed_url:
            return []
        xml_text = self._request_text(self.source.feed_url, settings)

        root = ET.fromstring(xml_text)
        items = self._extract_feed_items(root)

        articles: list[RawArticle] = []
        for item in items[: settings.max_items_per_source]:
            title = self._item_title(item)
            link = self._item_link(item)
            if not title or not link:
                continue

            published_raw = self._item_published(item)
            snippet_raw = self._item_snippet(item)
            image_url = self._item_image(item)

            articles.append(
                RawArticle(
                    source_id=self.source.id,
                    title=title,
                    url=canonicalize_url(link, self.source.base_url),
                    published_at_utc=parse_datetime_to_utc(published_raw),
                    snippet=strip_html(snippet_raw or ""),
                    image_url=canonicalize_url(image_url, self.source.base_url)
                    if image_url
                    else None,
                )
            )

        return self._dedupe_by_url(articles)

    def _fetch_from_listing(self, settings: Settings) -> list[RawArticle]:
        html = self._request_text(self.source.listing_url, settings)
        soup = BeautifulSoup(html, "html.parser")

        articles: list[RawArticle] = []
        meta_fetch_budget = settings.article_meta_fetch_budget

        cards = soup.select(self.source.article_selector)
        for card in cards[: settings.max_items_per_source]:
            link_node = card.select_one(self.source.link_selector)
            if not link_node:
                continue

            href = link_node.get("href")
            if not href:
                continue

            title = (link_node.get_text(" ", strip=True) or "").strip()
            if not title:
                continue

            raw_url = canonicalize_url(urljoin(self.source.base_url, href))
            time_node = card.select_one(self.source.time_selector)
            time_raw = (
                time_node.get("datetime")
                if time_node and time_node.has_attr("datetime")
                else (time_node.get_text(" ", strip=True) if time_node else None)
            )
            published_at = parse_datetime_to_utc(time_raw)

            snippet_node = card.select_one(self.source.snippet_selector)
            snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""

            image_node = card.select_one(self.source.image_selector)
            image_url = image_node.get("src") if image_node else None

            if (published_at is None or not snippet or not image_url) and meta_fetch_budget > 0:
                meta_fetch_budget -= 1
                meta = self._fetch_article_meta(raw_url, settings)
                if published_at is None:
                    published_at = meta.get("published_at_utc")
                if not snippet:
                    snippet = meta.get("snippet") or ""
                if not image_url:
                    image_url = meta.get("image_url")

            articles.append(
                RawArticle(
                    source_id=self.source.id,
                    title=title,
                    url=raw_url,
                    published_at_utc=published_at,
                    snippet=strip_html(snippet),
                    image_url=canonicalize_url(image_url, self.source.base_url)
                    if image_url
                    else None,
                )
            )

        return self._dedupe_by_url(articles)

    def _fetch_article_meta(self, article_url: str, settings: Settings) -> dict:
        try:
            html = self._request_text(article_url, settings)
        except Exception:
            return {}

        soup = BeautifulSoup(html, "html.parser")

        published_raw = None
        for selector in (
            "meta[property='article:published_time']",
            "meta[name='pubdate']",
            "meta[name='publish-date']",
            "time[datetime]",
        ):
            node = soup.select_one(selector)
            if not node:
                continue
            if node.name == "time":
                published_raw = node.get("datetime") or node.get_text(" ", strip=True)
            else:
                published_raw = node.get("content")
            if published_raw:
                break

        snippet = ""
        snippet_node = soup.select_one("meta[name='description']")
        if snippet_node and snippet_node.get("content"):
            snippet = snippet_node.get("content", "")
        elif soup.select_one("p"):
            snippet = soup.select_one("p").get_text(" ", strip=True)

        image_url = None
        image_node = soup.select_one("meta[property='og:image']")
        if image_node and image_node.get("content"):
            image_url = image_node.get("content")

        return {
            "published_at_utc": parse_datetime_to_utc(published_raw),
            "snippet": strip_html(snippet),
            "image_url": image_url,
        }

    def _request_text(self, url: str, settings: Settings) -> str:
        session = self._build_session(settings)
        response = session.get(
            url,
            headers={"User-Agent": settings.user_agent},
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        return response.text

    @staticmethod
    def _build_session(settings: Settings) -> requests.Session:
        retries = Retry(
            total=settings.request_retries,
            connect=settings.request_retries,
            read=settings.request_retries,
            status=settings.request_retries,
            backoff_factor=0.4,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
        )
        adapter = HTTPAdapter(max_retries=retries)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def _dedupe_by_url(articles: list[RawArticle]) -> list[RawArticle]:
        deduped: dict[str, RawArticle] = {}
        for article in articles:
            deduped[article.url] = article
        return list(deduped.values())

    @staticmethod
    def _extract_feed_items(root: ET.Element) -> list[ET.Element]:
        channel = root.find("channel")
        if channel is not None:
            return channel.findall("item")
        return [node for node in root.iter() if BaseSourceAdapter._local_name(node.tag) == "entry"]

    @staticmethod
    def _local_name(tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    def _item_title(self, item: ET.Element) -> Optional[str]:
        return self._direct_text(item, {"title"})

    def _item_link(self, item: ET.Element) -> Optional[str]:
        direct_link = self._direct_text(item, {"link"})
        if direct_link:
            return direct_link

        for child in item:
            if self._local_name(child.tag) != "link":
                continue
            href = child.attrib.get("href")
            rel = child.attrib.get("rel", "alternate")
            if href and rel in {"alternate", ""}:
                return href

        guid = self._direct_text(item, {"guid"})
        if guid and guid.startswith("http"):
            return guid
        return None

    def _item_published(self, item: ET.Element) -> Optional[str]:
        return self._direct_text(item, {"pubDate", "published", "updated", "dc:date", "date"})

    def _item_snippet(self, item: ET.Element) -> Optional[str]:
        return self._direct_text(item, {"description", "summary", "content", "content:encoded"})

    def _item_image(self, item: ET.Element) -> Optional[str]:
        for child in item.iter():
            name = self._local_name(child.tag)
            if name in {"content", "thumbnail", "enclosure"}:
                image_url = pick_first([child.attrib.get("url"), child.attrib.get("href")])
                if image_url:
                    return image_url

        snippet = self._item_snippet(item)
        if snippet:
            soup = BeautifulSoup(snippet, "html.parser")
            img = soup.select_one("img")
            if img and img.get("src"):
                return img.get("src")

        return None

    def _direct_text(self, item: ET.Element, names: set[str]) -> Optional[str]:
        lowered = {value.lower() for value in names}

        for child in item:
            local = self._local_name(child.tag).lower()
            if local in lowered and child.text and child.text.strip():
                return child.text.strip()

        for child in item.iter():
            local = self._local_name(child.tag).lower()
            if local in lowered and child.text and child.text.strip():
                return child.text.strip()

        return None
