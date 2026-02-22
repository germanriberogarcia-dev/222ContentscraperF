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
from app.services.ingestion import IngestionService
from app.utils import to_iso_utc, utc_now


def main() -> int:
    settings = load_settings()
    try:
        from app.source_adapters.registry import build_source_adapters
    except ModuleNotFoundError as exc:
        print(
            json.dumps(
                {
                    "accepted": False,
                    "message": f"missing dependency: {exc.name}",
                    "run": None,
                },
                indent=2,
            )
        )
        return 1

    adapters = build_source_adapters()

    db.bootstrap_database(
        db_path=settings.db_path,
        sources=[adapter.source for adapter in adapters],
        now_iso_utc=to_iso_utc(utc_now()),
    )

    service = IngestionService(settings=settings, adapters=adapters)
    accepted, run, message = service.run_once(trigger="cli")

    payload = {
        "accepted": accepted,
        "message": message,
        "run": run,
    }
    print(json.dumps(payload, indent=2))

    if not accepted:
        return 1
    if run and run.get("status") == "failed":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
