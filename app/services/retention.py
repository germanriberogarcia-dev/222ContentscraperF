from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from app.db import cleanup_unsaved_older_than
from app.utils import to_iso_utc


def apply_retention(conn: sqlite3.Connection, *, now_utc: datetime, window_hours: int) -> int:
    cutoff = now_utc.astimezone(timezone.utc) - timedelta(hours=window_hours)
    cutoff_iso = to_iso_utc(cutoff)
    return cleanup_unsaved_older_than(conn, cutoff_iso)
