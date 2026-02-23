from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import db
from app.api.routes_articles import router as articles_router
from app.api.routes_health import router as health_router
from app.api.routes_ingestion import router as ingestion_router
from app.config import Settings, load_settings
from app.services.ingestion import IngestionService
from app.services.scheduler import DailyUtcScheduler
from app.source_adapters.registry import build_source_adapters
from app.utils import to_iso_utc, utc_now

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Coffee News Ingestion API", version="1.0.0")
BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = BASE_DIR / "frontend" / "scrape_dashboard_profile.html"
DASHBOARD_ASSETS_DIR = BASE_DIR / "frontend" / "assets"

if DASHBOARD_ASSETS_DIR.exists():
    app.mount(
        "/dashboard-assets",
        StaticFiles(directory=str(DASHBOARD_ASSETS_DIR)),
        name="dashboard-assets",
    )


@app.on_event("startup")
def startup_event() -> None:
    settings: Settings = load_settings()
    logger.info(
        "startup_config db_path=%s scheduler_enabled=%s vercel=%s commit=%s",
        settings.db_path,
        settings.scheduler_enabled,
        os.getenv("VERCEL", ""),
        os.getenv("VERCEL_GIT_COMMIT_SHA", ""),
    )
    adapters = build_source_adapters()

    db.bootstrap_database(
        db_path=settings.db_path,
        sources=[adapter.source for adapter in adapters],
        now_iso_utc=to_iso_utc(utc_now()),
    )

    ingestion_service = IngestionService(settings=settings, adapters=adapters)

    scheduler = DailyUtcScheduler(
        hour_utc=settings.schedule_hour_utc,
        minute_utc=settings.schedule_minute_utc,
        callback=lambda: ingestion_service.run_once(trigger="scheduler"),
    )

    if settings.scheduler_enabled:
        scheduler.start()
        logger.info(
            "scheduler_started hour_utc=%s minute_utc=%s",
            settings.schedule_hour_utc,
            settings.schedule_minute_utc,
        )

    app.state.settings = settings
    app.state.adapters = adapters
    app.state.ingestion_service = ingestion_service
    app.state.scheduler = scheduler


@app.on_event("shutdown")
def shutdown_event() -> None:
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler:
        scheduler.stop()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "coffee-news-ingestion-api",
        "status": "ok",
        "dashboard": "/dashboard",
        "docs": "/docs",
    }


@app.get("/dashboard", include_in_schema=False)
@app.get("/dashboard/", include_in_schema=False)
def dashboard() -> FileResponse:
    if not DASHBOARD_FILE.exists():
        raise HTTPException(status_code=404, detail="dashboard file not found")
    return FileResponse(str(DASHBOARD_FILE))


app.include_router(articles_router, prefix="/api")
app.include_router(ingestion_router, prefix="/api")
app.include_router(health_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    settings = load_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )
