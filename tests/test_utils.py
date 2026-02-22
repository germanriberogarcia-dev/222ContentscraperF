from __future__ import annotations

import unittest

from app.utils import article_id_from_canonical, canonicalize_url, parse_datetime_to_utc


class UtilsTestCase(unittest.TestCase):
    def test_canonicalize_url_strips_tracking(self) -> None:
        url = "https://Example.com/news/story/?utm_source=x&utm_medium=y&id=42#top"
        self.assertEqual(canonicalize_url(url), "https://example.com/news/story?id=42")

    def test_article_id_is_deterministic(self) -> None:
        canonical = "https://example.com/news/story"
        self.assertEqual(article_id_from_canonical(canonical), article_id_from_canonical(canonical))

    def test_parse_datetime_to_utc(self) -> None:
        parsed = parse_datetime_to_utc("2026-02-21T12:30:00-05:00")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.isoformat(), "2026-02-21T17:30:00+00:00")


if __name__ == "__main__":
    unittest.main()
