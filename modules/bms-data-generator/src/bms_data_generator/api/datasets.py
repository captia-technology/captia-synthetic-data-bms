"""Dataset endpoints: export de dumps."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from bms_data_generator.config import get_settings
from bms_data_generator.services.dump_service import DumpService

_router = APIRouter(prefix="/v1/datasets", tags=["datasets"])

# Lazy singleton: evita ejecutar mkdir(output_dir) en import time. Crítico
# en tests: defaults Linux (/app/output) fallan en Windows con PermissionError
# antes incluso de poder ejecutar conftest fixtures.
_service: DumpService | None = None


def _ensure_service() -> DumpService:
    global _service
    if _service is None:
        _service = DumpService(output_dir=get_settings().output_dir)
    return _service


def _verify_token(authorization: Annotated[str | None, Header()] = None) -> None:
    settings = get_settings()
    if not settings.api_token:
        return
    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class ExportRequest(BaseModel):
    months: int = Field(ge=1, le=24)
    format: str = Field(pattern="^(line_protocol|csv_long)$")
    include_faults: bool = False
    config_path: str | None = None


@_router.post(
    "/export",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_verify_token)],
)
async def export(req: ExportRequest) -> dict:
    try:
        job_id, output_path = _ensure_service().export(
            months=req.months,
            format=req.format,
            include_faults=req.include_faults,
            config_path=req.config_path,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "validation_failed", "message": str(exc)},
        ) from exc
    return {"job_id": job_id, "output_path": str(output_path)}


@_router.get("/jobs/{job_id}", dependencies=[Depends(_verify_token)])
async def get_job(job_id: str) -> dict:
    try:
        return _ensure_service().get(job_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"job_id {job_id} not found"},
        ) from exc


def get_router() -> APIRouter:
    return _router


def get_service() -> DumpService:
    return _ensure_service()


def reset_service_cache() -> None:
    """Test helper: dispara re-creación del servicio en próximo get_service()."""
    global _service
    _service = None
