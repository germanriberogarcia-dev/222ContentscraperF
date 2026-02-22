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
from app.utils import to_iso_utc, utc_now


def main() -> int:
    settings = load_settings()
    try:
        from app.source_adapters.registry import build_source_adapters
    except ModuleNotFoundError as exc:
        print(
            json.dumps(
                {
                    "timestamp_utc": to_iso_utc(utc_now()),
                    "latest_run": None,
                    "sources": [],
                    "error": f"missing dependency: {exc.name}",
                },
                indent=2,
            )
        )
        return 1

    adapters = build_source_adapters()

    checks = [adapter.check_health(settings) for adapter in adapters]
    with db.connection(settings.db_path) as conn:
        latest = db.latest_ingestion_run(conn)

    payload = {
        "timestamp_utc": to_iso_utc(utc_now()),
        "latest_run": dict(latest) if latest else None,
        "sources": [
            {
                "source_id": check.source_id,
                "source_name": check.source_name,
                "status": check.status,
                "checked_at_utc": check.checked_at_utc,
                "detail": check.detail,
            }
            for check in checks
        ],
    }

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
