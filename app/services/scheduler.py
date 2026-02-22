from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Callable

from app.utils import to_iso_utc

logger = logging.getLogger(__name__)


class DailyUtcScheduler:
    def __init__(self, *, hour_utc: int, minute_utc: int, callback: Callable[[], None]):
        self.hour_utc = hour_utc
        self.minute_utc = minute_utc
        self.callback = callback
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="daily-utc-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            now_utc = datetime.now(timezone.utc)
            next_run = now_utc.replace(
                hour=self.hour_utc,
                minute=self.minute_utc,
                second=0,
                microsecond=0,
            )
            if next_run <= now_utc:
                next_run = next_run + timedelta(days=1)

            sleep_seconds = max(1, int((next_run - now_utc).total_seconds()))
            logger.info("scheduler_sleep_until=%s", to_iso_utc(next_run))
            if self._stop_event.wait(timeout=sleep_seconds):
                break

            try:
                self.callback()
            except Exception:  # pragma: no cover
                logger.exception("scheduled_ingestion_failed")
