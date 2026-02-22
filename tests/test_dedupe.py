from __future__ import annotations

import tempfile
import unittest

from app import db
from app.models import NormalizedArticle, SourceConfig
from app.utils import article_id_from_canonical, to_iso_utc, utc_now


class DedupeTestCase(unittest.TestCase):
    def test_upsert_by_canonical_url(self) -> None:
        now = utc_now()
        canonical = "https://example.com/article-1"

        with tempfile.TemporaryDirectory() as tmp:
            db_path = f"{tmp}/test.db"
            source = SourceConfig(
                id="test_source",
                name="Test Source",
                base_url="https://example.com",
                feed_url=None,
                listing_url="https://example.com/news",
            )
            db.bootstrap_database(db_path=db_path, sources=[source], now_iso_utc=to_iso_utc(now))

            with db.connection(db_path) as conn:
                first = NormalizedArticle(
                    id=article_id_from_canonical(canonical),
                    source_id="test_source",
                    title="Initial",
                    url=canonical,
                    canonical_url=canonical,
                    published_at_utc=to_iso_utc(now),
                    snippet="A",
                    image_url=None,
                    first_seen_at_utc=to_iso_utc(now),
                    last_seen_at_utc=to_iso_utc(now),
                )
                second = NormalizedArticle(
                    id=article_id_from_canonical(canonical),
                    source_id="test_source",
                    title="Updated",
                    url=canonical,
                    canonical_url=canonical,
                    published_at_utc=to_iso_utc(now),
                    snippet="B",
                    image_url="https://example.com/image.jpg",
                    first_seen_at_utc=to_iso_utc(now),
                    last_seen_at_utc=to_iso_utc(now),
                )

                self.assertEqual(db.upsert_article(conn, first, to_iso_utc(now)), "inserted")
                self.assertEqual(db.upsert_article(conn, second, to_iso_utc(now)), "updated")

                rows = conn.execute("SELECT COUNT(*) AS count FROM articles").fetchone()
                self.assertEqual(rows["count"], 1)

                article_row = conn.execute(
                    "SELECT title, snippet, image_url FROM articles WHERE canonical_url = ?",
                    (canonical,),
                ).fetchone()
                self.assertEqual(article_row["title"], "Updated")
                self.assertEqual(article_row["snippet"], "B")
                self.assertEqual(article_row["image_url"], "https://example.com/image.jpg")


if __name__ == "__main__":
    unittest.main()
