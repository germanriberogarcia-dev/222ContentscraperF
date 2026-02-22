from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas import SourceHealthOut, SourceHealthResponse
from app.utils import to_iso_utc, utc_now

router = APIRouter(tags=["health"])


@router.get("/sources/health", response_model=SourceHealthResponse)
def sources_health(request: Request):
    settings = request.app.state.settings
    adapters = request.app.state.adapters

    checks = [adapter.check_health(settings) for adapter in adapters]
    sources = [
        SourceHealthOut(
            source_id=check.source_id,
            source_name=check.source_name,
            status=check.status,
            checked_at_utc=check.checked_at_utc,
            detail=check.detail,
        )
        for check in checks
    ]

    return SourceHealthResponse(timestamp_utc=to_iso_utc(utc_now()), sources=sources)
