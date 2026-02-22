from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from app.models import NormalizedArticle, SourceConfig

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  base_url TEXT NOT NULL,
  feed_url TEXT,
  scraper_enabled INTEGER NOT NULL DEFAULT 1,
  active INTEGER NOT NULL DEFAULT 1,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS articles (
  id TEXT PRIMARY KEY,
  canonical_url TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  source_id TEXT NOT NULL,
  published_at_utc TEXT NOT NULL,
  snippet TEXT,
  image_url TEXT,
  is_saved INTEGER NOT NULL DEFAULT 0,
  first_seen_at_utc TEXT NOT NULL,
  last_seen_at_utc TEXT NOT NULL,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL,
  FOREIGN KEY (source_id) REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
  id TEXT PRIMARY KEY,
  started_at_utc TEXT NOT NULL,
  completed_at_utc TEXT,
  status TEXT NOT NULL,
  new_count INTEGER NOT NULL DEFAULT 0,
  updated_count INTEGER NOT NULL DEFAULT 0,
  skipped_count INTEGER NOT NULL DEFAULT 0,
  error_count INTEGER NOT NULL DEFAULT 0,
  notes TEXT
);
"""


@contextmanager
def connection(db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)


def seed_sources(conn: sqlite3.Connection, sources: Iterable[SourceConfig], now_utc: str) -> None:
    for source in sources:
        conn.execute(
            """
            INSERT INTO sources (
                id, name, base_url, feed_url, scraper_enabled, active, created_at_utc, updated_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                base_url = excluded.base_url,
                feed_url = excluded.feed_url,
                scraper_enabled = excluded.scraper_enabled,
                active = excluded.active,
                updated_at_utc = excluded.updated_at_utc
            """,
            (
                source.id,
                source.name,
                source.base_url,
                source.feed_url,
                1 if source.scraper_enabled else 0,
                1 if source.active else 0,
                now_utc,
                now_utc,
            ),
        )


def upsert_article(conn: sqlite3.Connection, article: NormalizedArticle, now_utc: str) -> str:
    existing = conn.execute(
        "SELECT id FROM articles WHERE canonical_url = ?",
        (article.canonical_url,),
    ).fetchone()

    if existing is None:
        conn.execute(
            """
            INSERT INTO articles (
                id, canonical_url, title, url, source_id, published_at_utc, snippet, image_url,
                is_saved, first_seen_at_utc, last_seen_at_utc, created_at_utc, updated_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (
                article.id,
                article.canonical_url,
                article.title,
                article.url,
                article.source_id,
                article.published_at_utc,
                article.snippet,
                article.image_url,
                article.first_seen_at_utc,
                article.last_seen_at_utc,
                now_utc,
                now_utc,
            ),
        )
        return "inserted"

    conn.execute(
        """
        UPDATE articles
        SET title = ?,
            url = ?,
            source_id = ?,
            published_at_utc = ?,
            snippet = ?,
            image_url = ?,
            last_seen_at_utc = ?,
            updated_at_utc = ?
        WHERE canonical_url = ?
        """,
        (
            article.title,
            article.url,
            article.source_id,
            article.published_at_utc,
            article.snippet,
            article.image_url,
            article.last_seen_at_utc,
            now_utc,
            article.canonical_url,
        ),
    )
    return "updated"


def list_articles(
    conn: sqlite3.Connection,
    *,
    cutoff_iso_utc: Optional[str],
    saved: str,
    source_id: Optional[str],
    limit: int,
    offset: int,
):
    where_clauses = []
    params: list[object] = []

    if saved == "true":
        where_clauses.append("a.is_saved = 1")
    elif saved == "false":
        where_clauses.append("a.is_saved = 0")

    if source_id:
        where_clauses.append("a.source_id = ?")
        params.append(source_id)

    # Saved-only view intentionally ignores cutoff so users can always see saved items.
    if cutoff_iso_utc and saved == "false":
        where_clauses.append("a.published_at_utc >= ?")
        params.append(cutoff_iso_utc)
    elif cutoff_iso_utc and saved == "all":
        # In all-mode, include active-window items plus any saved items regardless of age.
        where_clauses.append("(a.is_saved = 1 OR a.published_at_utc >= ?)")
        params.append(cutoff_iso_utc)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    total_row = conn.execute(
        f"""
        SELECT COUNT(*) AS total
        FROM articles a
        {where_sql}
        """,
        tuple(params),
    ).fetchone()
    total = int(total_row["total"] if total_row else 0)

    rows = conn.execute(
        f"""
        SELECT
            a.id,
            a.source_id,
            s.name AS source_name,
            a.title,
            a.url,
            a.canonical_url,
            a.published_at_utc,
            a.snippet,
            a.image_url,
            a.is_saved,
            a.first_seen_at_utc,
            a.last_seen_at_utc
        FROM articles a
        INNER JOIN sources s ON s.id = a.source_id
        {where_sql}
        ORDER BY a.published_at_utc DESC, a.updated_at_utc DESC
        LIMIT ? OFFSET ?
        """,
        tuple([*params, limit, offset]),
    ).fetchall()

    return total, rows


def set_article_saved(conn: sqlite3.Connection, article_id: str, is_saved: bool) -> bool:
    result = conn.execute(
        "UPDATE articles SET is_saved = ?, updated_at_utc = ? WHERE id = ?",
        (1 if is_saved else 0, datetime.utcnow().replace(microsecond=0).isoformat() + "Z", article_id),
    )
    return result.rowcount > 0


def delete_article(conn: sqlite3.Connection, article_id: str) -> bool:
    result = conn.execute(
        "DELETE FROM articles WHERE id = ?",
        (article_id,),
    )
    return result.rowcount > 0


def create_ingestion_run(conn: sqlite3.Connection, run_id: str, started_at_utc: str, notes: Optional[dict] = None) -> None:
    conn.execute(
        """
        INSERT INTO ingestion_runs (
            id, started_at_utc, status, new_count, updated_count, skipped_count, error_count, notes
        ) VALUES (?, ?, 'running', 0, 0, 0, 0, ?)
        """,
        (run_id, started_at_utc, json.dumps(notes or {})),
    )


def complete_ingestion_run(
    conn: sqlite3.Connection,
    run_id: str,
    *,
    completed_at_utc: str,
    status: str,
    new_count: int,
    updated_count: int,
    skipped_count: int,
    error_count: int,
    notes: Optional[dict] = None,
) -> None:
    conn.execute(
        """
        UPDATE ingestion_runs
        SET completed_at_utc = ?,
            status = ?,
            new_count = ?,
            updated_count = ?,
            skipped_count = ?,
            error_count = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            completed_at_utc,
            status,
            new_count,
            updated_count,
            skipped_count,
            error_count,
            json.dumps(notes or {}),
            run_id,
        ),
    )


def get_ingestion_run(conn: sqlite3.Connection, run_id: str):
    return conn.execute(
        """
        SELECT id, started_at_utc, completed_at_utc, status, new_count, updated_count, skipped_count, error_count, notes
        FROM ingestion_runs
        WHERE id = ?
        """,
        (run_id,),
    ).fetchone()


def latest_ingestion_run(conn: sqlite3.Connection):
    return conn.execute(
        """
        SELECT id, started_at_utc, completed_at_utc, status, new_count, updated_count, skipped_count, error_count, notes
        FROM ingestion_runs
        ORDER BY started_at_utc DESC
        LIMIT 1
        """
    ).fetchone()


def cleanup_unsaved_older_than(conn: sqlite3.Connection, cutoff_iso_utc: str) -> int:
    result = conn.execute(
        "DELETE FROM articles WHERE is_saved = 0 AND published_at_utc < ?",
        (cutoff_iso_utc,),
    )
    return int(result.rowcount)


def bootstrap_database(db_path: str, sources: Iterable[SourceConfig], now_iso_utc: str) -> None:
    with connection(db_path) as conn:
        init_db(conn)
        seed_sources(conn, sources, now_iso_utc)
