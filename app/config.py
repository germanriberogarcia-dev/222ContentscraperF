from __future__ import annotations

import errno
import logging
import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ENV_PATH = ".env"
FALLBACK_DB_PATH = "/tmp/coffee_news.db"
logger = logging.getLogger(__name__)


def _load_dotenv(path: str = DEFAULT_ENV_PATH) -> None:
    env_file = Path(path)
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"").strip("'")
        os.environ.setdefault(key, value)


def _as_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def _as_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _is_vercel_runtime() -> bool:
    # Vercel exposes VERCEL=1 (and related vars) at runtime.
    return os.getenv("VERCEL") == "1" or bool(os.getenv("VERCEL_ENV"))


def _resolve_db_path(db_path: str, *, is_vercel: bool) -> str:
    db_dir = Path(db_path).parent
    if str(db_dir) in {"", "."}:
        return db_path

    try:
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_path
    except OSError as exc:
        allow_fallback = is_vercel or exc.errno in {errno.EROFS, errno.EACCES}
        if not allow_fallback or db_path == FALLBACK_DB_PATH:
            raise

        Path(FALLBACK_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        logger.warning(
            "db_path_unwritable configured=%s fallback=%s errno=%s",
            db_path,
            FALLBACK_DB_PATH,
            exc.errno,
        )
        return FALLBACK_DB_PATH


@dataclass(frozen=True)
class Settings:
    db_path: str
    user_agent: str
    request_timeout_seconds: int
    request_retries: int
    ingestion_window_hours: int
    max_items_per_source: int
    article_meta_fetch_budget: int
    scheduler_enabled: bool
    schedule_hour_utc: int
    schedule_minute_utc: int
    app_host: str
    app_port: int



def load_settings(env_path: str = DEFAULT_ENV_PATH) -> Settings:
    is_vercel = _is_vercel_runtime()
    if not is_vercel:
        _load_dotenv(env_path)

    db_path = os.getenv("DB_PATH", FALLBACK_DB_PATH if is_vercel else "data/coffee_news.db")
    db_path = _resolve_db_path(db_path, is_vercel=is_vercel)
    scheduler_default = not is_vercel

    settings = Settings(
        db_path=db_path,
        user_agent=os.getenv(
            "USER_AGENT",
            "AntigravityCoffeeIngestionBot/1.0 (+https://antigravity.local)",
        ),
        request_timeout_seconds=_as_int("REQUEST_TIMEOUT_SECONDS", 15),
        request_retries=_as_int("REQUEST_RETRIES", 2),
        ingestion_window_hours=_as_int("INGESTION_WINDOW_HOURS", 24),
        max_items_per_source=_as_int("MAX_ITEMS_PER_SOURCE", 50),
        article_meta_fetch_budget=_as_int("ARTICLE_META_FETCH_BUDGET", 8),
        scheduler_enabled=_as_bool("SCHEDULER_ENABLED", scheduler_default),
        schedule_hour_utc=_as_int("SCHEDULE_HOUR_UTC", 0),
        schedule_minute_utc=_as_int("SCHEDULE_MINUTE_UTC", 15),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=_as_int("APP_PORT", 8000),
    )

    return settings
