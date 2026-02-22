from __future__ import annotations

import json
import threading
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app import db
from app.config import Settings
from app.models import NormalizedArticle, RawArticle
from app.services.retention import apply_retention
from app.utils import article_id_from_canonical, canonicalize_url, to_iso_utc, utc_now


class IngestionService:
    def __init__(self, settings: Settings, adapters: list[Any]):
        self.settings = settings
        self.adapters = adapters
        self._lock = threading.Lock()

    def is_running(self) -> bool:
        return self._lock.locked()

    def run_once(self, *, trigger: str = "manual") -> tuple[bool, dict[str, Any] | None, str]:
        acquired = self._lock.acquire(blocking=False)
        if not acquired:
            return False, None, "ingestion already running"

        run_id = str(uuid4())
        started_at = utc_now()
        started_iso = to_iso_utc(started_at)

        try:
            with db.connection(self.settings.db_path) as conn:
                db.create_ingestion_run(
                    conn,
                    run_id,
                    started_iso,
                    notes={"trigger": trigger, "warnings": []},
                )

            result = self._execute_run(run_id=run_id, started_at=started_at, trigger=trigger)
            return True, result, "ok"
        finally:
            self._lock.release()

    def _execute_run(self, *, run_id: str, started_at: datetime, trigger: str) -> dict[str, Any]:
        now_utc = utc_now()
        cutoff = now_utc - timedelta(hours=self.settings.ingestion_window_hours)

        records_in = 0
        records_out = 0
        new_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        warnings: list[str] = []

        try:
            with db.connection(self.settings.db_path) as conn:
                for adapter in self.adapters:
                    try:
                        fetched, adapter_warnings = adapter.fetch(self.settings)
                        records_in += len(fetched)
                        warnings.extend([f"{adapter.source.id}: {w}" for w in adapter_warnings])

                        for raw in fetched:
                            action = self._upsert_if_in_window(
                                conn=conn,
                                raw=raw,
                                now_utc=now_utc,
                                cutoff_utc=cutoff,
                            )
                            if action == "inserted":
                                new_count += 1
                                records_out += 1
                            elif action == "updated":
                                updated_count += 1
                                records_out += 1
                            else:
                                skipped_count += 1
                    except Exception as exc:
                        error_count += 1
                        warnings.append(f"{adapter.source.id}: ingestion_error={exc}")

                removed_count = apply_retention(
                    conn,
                    now_utc=now_utc,
                    window_hours=self.settings.ingestion_window_hours,
                )

                if error_count >= len(self.adapters):
                    status = "failed"
                elif error_count > 0:
                    status = "partial_failure"
                else:
                    status = "success"

                notes = {
                    "trigger": trigger,
                    "records_in": records_in,
                    "records_out": records_out,
                    "removed_count": removed_count,
                    "warnings": warnings,
                }

                db.complete_ingestion_run(
                    conn,
                    run_id,
                    completed_at_utc=to_iso_utc(utc_now()),
                    status=status,
                    new_count=new_count,
                    updated_count=updated_count,
                    skipped_count=skipped_count,
                    error_count=error_count,
                    notes=notes,
                )

                row = db.get_ingestion_run(conn, run_id)
                return _run_row_to_dict(row)
        except Exception as exc:
            # Ensure run is finalized in DB even if a fatal error occurs.
            with db.connection(self.settings.db_path) as conn:
                db.complete_ingestion_run(
                    conn,
                    run_id,
                    completed_at_utc=to_iso_utc(utc_now()),
                    status="failed",
                    new_count=new_count,
                    updated_count=updated_count,
                    skipped_count=skipped_count,
                    error_count=error_count + 1,
                    notes={"trigger": trigger, "warnings": [f"fatal: {exc}"]},
                )
                row = db.get_ingestion_run(conn, run_id)
                return _run_row_to_dict(row)

    def _upsert_if_in_window(
        self,
        *,
        conn,
        raw: RawArticle,
        now_utc: datetime,
        cutoff_utc: datetime,
    ) -> str:
        if raw.published_at_utc is None:
            return "skipped"

        published_utc = raw.published_at_utc.astimezone(timezone.utc)
        if published_utc < cutoff_utc:
            return "skipped"

        canonical = canonicalize_url(raw.url)
        normalized = NormalizedArticle(
            id=article_id_from_canonical(canonical),
            source_id=raw.source_id,
            title=raw.title.strip(),
            url=canonicalize_url(raw.url),
            canonical_url=canonical,
            published_at_utc=to_iso_utc(published_utc),
            snippet=raw.snippet.strip(),
            image_url=canonicalize_url(raw.image_url) if raw.image_url else None,
            first_seen_at_utc=to_iso_utc(now_utc),
            last_seen_at_utc=to_iso_utc(now_utc),
        )
        return db.upsert_article(conn, normalized, to_iso_utc(now_utc))

    def latest_status(self) -> dict[str, Any]:
        with db.connection(self.settings.db_path) as conn:
            row = db.latest_ingestion_run(conn)
        return {
            "running": self.is_running(),
            "last_run": _run_row_to_dict(row) if row else None,
        }


def _run_row_to_dict(row) -> dict[str, Any]:
    notes_raw = row["notes"]
    try:
        notes = json.loads(notes_raw) if notes_raw else {}
    except Exception:
        notes = {"raw": notes_raw}

    return {
        "id": row["id"],
        "started_at_utc": row["started_at_utc"],
        "completed_at_utc": row["completed_at_utc"],
        "status": row["status"],
        "new_count": row["new_count"],
        "updated_count": row["updated_count"],
        "skipped_count": row["skipped_count"],
        "error_count": row["error_count"],
        "notes": notes,
    }
