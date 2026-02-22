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
        print(json.dumps({"ok": False, "error": f"missing dependency: {exc.name}"}, indent=2))
        return 1

    adapters = build_source_adapters()

    db.bootstrap_database(
        db_path=settings.db_path,
        sources=[adapter.source for adapter in adapters],
        now_iso_utc=to_iso_utc(utc_now()),
    )

    checks = [adapter.check_health(settings) for adapter in adapters]
    failures = [check for check in checks if check.status != "ok"]

    payload = {
        "timestamp_utc": to_iso_utc(utc_now()),
        "db_path": settings.db_path,
        "sources": [
            {
                "source_id": check.source_id,
                "source_name": check.source_name,
                "status": check.status,
                "detail": check.detail,
            }
            for check in checks
        ],
        "ok": len(failures) == 0,
    }

    print(json.dumps(payload, indent=2))
    return 0 if len(failures) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
