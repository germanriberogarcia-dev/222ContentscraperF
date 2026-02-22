from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas import IngestionRunOut, IngestionStatusResponse, TriggerResponse

router = APIRouter(tags=["ingestion"])


@router.post("/ingestion/run", response_model=TriggerResponse)
def run_ingestion(request: Request):
    service = request.app.state.ingestion_service
    accepted, run, message = service.run_once(trigger="manual")

    if not accepted:
        raise HTTPException(status_code=409, detail=message)

    return TriggerResponse(accepted=True, message=message, run=IngestionRunOut(**run))


@router.get("/ingestion/status", response_model=IngestionStatusResponse)
def ingestion_status(request: Request):
    service = request.app.state.ingestion_service
    snapshot = service.latest_status()

    if snapshot["last_run"] is None:
        return IngestionStatusResponse(running=snapshot["running"], last_run=None)

    return IngestionStatusResponse(
        running=snapshot["running"],
        last_run=IngestionRunOut(**snapshot["last_run"]),
    )
