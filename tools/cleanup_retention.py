#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import db
from app.config import load_settings
from app.services.retention import apply_retention
from app.utils import to_iso_utc, utc_now


def main() -> int:
    settings = load_settings()
    now_utc = utc_now()

    db.bootstrap_database(
        db_path=settings.db_path,
        sources=[],
        now_iso_utc=to_iso_utc(now_utc),
    )

    with db.connection(settings.db_path) as conn:
        removed = apply_retention(
            conn,
            now_utc=now_utc,
            window_hours=settings.ingestion_window_hours,
        )

    print(
        json.dumps(
            {
                "timestamp_utc": to_iso_utc(now_utc),
                "window_hours": settings.ingestion_window_hours,
                "removed": removed,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
