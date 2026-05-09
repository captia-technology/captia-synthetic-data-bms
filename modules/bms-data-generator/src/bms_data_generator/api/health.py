"""Health, readiness, metrics endpoints (públicos)."""

from __future__ import annotations

import time

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST

from bms_data_generator import __version__
from bms_data_generator.metrics import metrics_text

_router = APIRouter()
_START_TIME = time.monotonic()
_state: dict = {"mqtt_connected": False, "config_loaded": True}


@_router.get("/healthz")
async def healthz() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "uptime": round(time.monotonic() - _START_TIME, 2),
    }


@_router.get("/readyz")
async def readyz(response: Response) -> dict:
    if not _state["mqtt_connected"] or not _state["config_loaded"]:
        response.status_code = 503
        return {"status": "not_ready", "checks": _state.copy()}
    return {"status": "ready", "checks": _state.copy()}


@_router.get("/metrics")
async def metrics() -> Response:
    return Response(content=metrics_text(), media_type=CONTENT_TYPE_LATEST)


def set_mqtt_connected(value: bool) -> None:
    _state["mqtt_connected"] = value


def set_config_loaded(value: bool) -> None:
    _state["config_loaded"] = value


def get_router() -> APIRouter:
    return _router
