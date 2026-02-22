from __future__ import annotations

import tempfile
import unittest
from datetime import timedelta

from app import db
from app.models import NormalizedArticle, SourceConfig
from app.utils import article_id_from_canonical, canonicalize_url, to_iso_utc, utc_now


class ListArticlesBehaviorTestCase(unittest.TestCase):
    def test_saved_all_includes_saved_outside_cutoff(self) -> None:
        now = utc_now()
        old_time = now - timedelta(hours=40)
        fresh_time = now - timedelta(hours=2)
        cutoff = to_iso_utc(now - timedelta(hours=24))

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

            old_saved_url = canonicalize_url("https://example.com/saved-old")
            old_unsaved_url = canonicalize_url("https://example.com/unsaved-old")
            fresh_unsaved_url = canonicalize_url("https://example.com/unsaved-fresh")

            with db.connection(db_path) as conn:
                for canonical_url, published_at, title in (
                    (old_saved_url, old_time, "Saved Old"),
                    (old_unsaved_url, old_time, "Unsaved Old"),
                    (fresh_unsaved_url, fresh_time, "Unsaved Fresh"),
                ):
                    article = NormalizedArticle(
                        id=article_id_from_canonical(canonical_url),
                        source_id="test_source",
                        title=title,
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

                total_all, rows_all = db.list_articles(
                    conn,
                    cutoff_iso_utc=cutoff,
                    saved="all",
                    source_id=None,
                    limit=50,
                    offset=0,
                )
                ids_all = {row["id"] for row in rows_all}

                total_unsaved, rows_unsaved = db.list_articles(
                    conn,
                    cutoff_iso_utc=cutoff,
                    saved="false",
                    source_id=None,
                    limit=50,
                    offset=0,
                )
                ids_unsaved = {row["id"] for row in rows_unsaved}

                total_saved, rows_saved = db.list_articles(
                    conn,
                    cutoff_iso_utc=cutoff,
                    saved="true",
                    source_id=None,
                    limit=50,
                    offset=0,
                )
                ids_saved = {row["id"] for row in rows_saved}

            old_saved_id = article_id_from_canonical(old_saved_url)
            old_unsaved_id = article_id_from_canonical(old_unsaved_url)
            fresh_unsaved_id = article_id_from_canonical(fresh_unsaved_url)

            self.assertEqual(total_all, 2)
            self.assertIn(old_saved_id, ids_all)
            self.assertIn(fresh_unsaved_id, ids_all)
            self.assertNotIn(old_unsaved_id, ids_all)

            self.assertEqual(total_unsaved, 1)
            self.assertIn(fresh_unsaved_id, ids_unsaved)

            self.assertEqual(total_saved, 1)
            self.assertIn(old_saved_id, ids_saved)

    def test_delete_article_removes_row(self) -> None:
        now = utc_now()

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

            url = canonicalize_url("https://example.com/delete-me")
            article_id = article_id_from_canonical(url)

            with db.connection(db_path) as conn:
                article = NormalizedArticle(
                    id=article_id,
                    source_id="test_source",
                    title="Delete Me",
                    url=url,
                    canonical_url=url,
                    published_at_utc=to_iso_utc(now),
                    snippet="Snippet",
                    image_url=None,
                    first_seen_at_utc=to_iso_utc(now),
                    last_seen_at_utc=to_iso_utc(now),
                )
                db.upsert_article(conn, article, to_iso_utc(now))

                self.assertTrue(db.delete_article(conn, article_id))
                self.assertFalse(db.delete_article(conn, article_id))

                row = conn.execute("SELECT id FROM articles WHERE id = ?", (article_id,)).fetchone()
                self.assertIsNone(row)


if __name__ == "__main__":
    unittest.main()
