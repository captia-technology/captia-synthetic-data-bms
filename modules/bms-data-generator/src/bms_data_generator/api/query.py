"""POST /v1/query — read-path equivalente al Dashboard Adapter de CENTINELA+.

Acepta una variable canónica + rango temporal y devuelve los puntos
agregados ya leídos del bucket InfluxDB que mejor encaja con la ventana
solicitada (hot path -> raw, ventanas largas -> rollup).
"""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from bms_data_generator.config import get_settings
from bms_data_generator.rate_limit import limiter
from bms_data_generator.services.query_service import (
    InfluxQueryClient,
    QueryRequest,
    build_flux,
    select_bucket,
)

_router = APIRouter(prefix="/v1", tags=["query"])


def _verify_token(authorization: Annotated[str | None, Header()] = None) -> None:
    settings = get_settings()
    if not settings.api_token:
        return
    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class QueryBody(BaseModel):
    variable: str = Field(min_length=1, max_length=120)
    start: str = "-1h"
    stop: str = "now()"
    asset_id: str | None = None
    domain_id: str = "bms_classrooms"
    aggregation: str = Field(default="mean", pattern="^(mean|max|min|sum|last|first|count)$")


class QueryResponse(BaseModel):
    bucket: str
    flux: str
    rows: list[dict]


def _build_client() -> InfluxQueryClient:
    # Para una read-API que corre dentro de Docker, INFLUXDB_URL=http://influxdb:8086.
    # Cuando el generator corre en host (`make run-host`), redirigimos al host port.
    url = os.environ.get("INFLUXDB_URL", "http://influxdb:8086")
    if url.startswith("http://influxdb:") and os.environ.get("BMS_RUNNING_ON_HOST", "").lower() in {
        "1",
        "true",
    }:
        port = os.environ.get("INFLUXDB_PORT_HOST", "8087")
        url = f"http://localhost:{port}"
    token = os.environ.get("INFLUXDB_TOKEN", "")
    org = os.environ.get("INFLUXDB_ORG", "captia")
    return InfluxQueryClient(url=url, token=token, org=org)


@_router.post("/query", response_model=QueryResponse, dependencies=[Depends(_verify_token)])
@limiter.limit("60/minute")
async def query(request: Request, body: QueryBody) -> QueryResponse:
    """Resolver una serie temporal canónica.

    El bucket lo elige la lógica de :func:`select_bucket` siguiendo el
    contrato CENTINELA+ § 1.3 (raw para ≤ 1 h, 1-min rollup para ≤ 24 h,
    15-min rollup para ≤ 7 d, 1-h rollup para ≤ 365 d).
    """
    bucket, is_rollup = select_bucket(body.start)
    try:
        flux = build_flux(
            QueryRequest(
                variable=body.variable,
                start=body.start,
                stop=body.stop,
                asset_id=body.asset_id,
                domain_id=body.domain_id,
                aggregation=body.aggregation,
            ),
            bucket=bucket,
            is_rollup=is_rollup,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "validation_failed", "message": str(exc)},
        ) from exc

    client = _build_client()
    if not client.token:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "not_configured",
                "message": "INFLUXDB_TOKEN not set; /v1/query cannot reach the database.",
            },
        )
    try:
        rows = await client.query(flux)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": "influx_error", "message": str(exc)},
        ) from exc
    return QueryResponse(bucket=bucket, flux=flux, rows=rows)


def get_router() -> APIRouter:
    return _router
