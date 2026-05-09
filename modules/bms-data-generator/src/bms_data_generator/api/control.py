"""Control endpoints (start/stop/status). Auth Bearer si BMS_API_TOKEN definido."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from bms_data_generator.config import get_settings
from bms_data_generator.rate_limit import limiter
from bms_data_generator.services.runner_service import RunnerService

_router = APIRouter(prefix="/v1/control", tags=["control"])
_service = RunnerService()


def _verify_token(authorization: Annotated[str | None, Header()] = None) -> None:
    settings = get_settings()
    if not settings.api_token:
        return
    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class StartRequest(BaseModel):
    config_path: str
    mode: str = Field(pattern="^(live|backfill)$")
    aulas: int = Field(ge=1, le=70)
    faults: list[str] = Field(default_factory=list)


@_router.post(
    "/start",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_verify_token)],
)
@limiter.limit("10/minute")
async def start(request: Request, req: StartRequest) -> dict:
    valid_faults = {"sensor_drift", "valve_stuck", "fan_failure", "refrigerant_low"}
    invalid = [f for f in req.faults if f not in valid_faults]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_failed",
                "message": f"Invalid fault types: {invalid}",
            },
        )
    try:
        job_id = _service.start(req.config_path, req.mode, req.aulas, req.faults)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409, detail={"error": "conflict", "message": str(exc)}
        ) from exc
    return {"job_id": job_id}


@_router.post("/stop", dependencies=[Depends(_verify_token)])
async def stop(job_id: str) -> dict:
    try:
        _service.stop(job_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"job_id {job_id} not found"},
        ) from exc
    return {"stopped": job_id}


@_router.get("/status")
async def get_status(job_id: str | None = None) -> dict:
    return _service.status(job_id)


def get_router() -> APIRouter:
    return _router


def get_service() -> RunnerService:
    """Acceso al singleton para tests."""
    return _service
