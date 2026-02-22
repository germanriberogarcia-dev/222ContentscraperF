from __future__ import annotations

import tempfile
import unittest
from datetime import timedelta

from app import db
from app.models import NormalizedArticle, SourceConfig
from app.services.retention import apply_retention
from app.utils import article_id_from_canonical, canonicalize_url, to_iso_utc, utc_now


class RetentionTestCase(unittest.TestCase):
    def test_unsaved_outside_window_is_removed_saved_is_kept(self) -> None:
        now = utc_now()
        old_time = now - timedelta(hours=30)
        fresh_time = now - timedelta(hours=2)

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

            old_unsaved_url = canonicalize_url("https://example.com/a")
            old_saved_url = canonicalize_url("https://example.com/b")
            fresh_unsaved_url = canonicalize_url("https://example.com/c")

            with db.connection(db_path) as conn:
                for canonical_url, published_at in (
                    (old_unsaved_url, old_time),
                    (old_saved_url, old_time),
                    (fresh_unsaved_url, fresh_time),
                ):
                    article = NormalizedArticle(
                        id=article_id_from_canonical(canonical_url),
                        source_id="test_source",
                        title="Title",
                        url=canonical_url,
                        canonical_url=canonical_url,
                        published_at_utc=to_iso_utc(published_at),
                        snippet="Snippet",
                        image_url=None,
                        first_seen_at_utc=to_iso_utc(now),
                        last_seen_at_utc=to_iso_utc(now),
                    )
                    db.upsert_article(conn, article, to_iso_utc(now))

                db.set_article_saved(conn, article_id_from_canonical(old_saved_url), True)

            with db.connection(db_path) as conn:
                removed = apply_retention(conn, now_utc=now, window_hours=24)
                self.assertEqual(removed, 1)

            with db.connection(db_path) as conn:
                remaining = conn.execute("SELECT id FROM articles").fetchall()
                remaining_ids = {row["id"] for row in remaining}

            self.assertNotIn(article_id_from_canonical(old_unsaved_url), remaining_ids)
            self.assertIn(article_id_from_canonical(old_saved_url), remaining_ids)
            self.assertIn(article_id_from_canonical(fresh_unsaved_url), remaining_ids)


if __name__ == "__main__":
    unittest.main()
