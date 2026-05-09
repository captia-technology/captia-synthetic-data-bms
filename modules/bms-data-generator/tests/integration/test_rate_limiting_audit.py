"""Auditoría de rate limiting en endpoints /v1/* (H-03 / slowapi).

Verifica que ``/v1/control/start`` y ``/v1/datasets/export`` aplican
límites por IP y que ``/healthz``, ``/readyz`` y ``/metrics`` no se
limitan.

Cierra el hallazgo H-03 (`AUDIT_REPORT.md`).
"""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

from bms_data_generator.config import reset_settings_cache
from bms_data_generator.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_limiter():
    """Limpia el storage en memoria del limiter entre tests."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def app(monkeypatch):
    """Build app with empty API token so /v1/* are reachable without Bearer."""
    monkeypatch.setenv("BMS_API_TOKEN", "")
    reset_settings_cache()
    from bms_data_generator.main import create_app
    yield create_app()
    reset_settings_cache()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoint_not_rate_limited(app):
    """``/healthz`` debe responder OK aunque hagamos 30 hits — sin limit."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        statuses = [(await ac.get("/healthz")).status_code for _ in range(30)]
    assert all(s == 200 for s in statuses), (
        f"/healthz tuvo respuestas no-200: {[s for s in statuses if s != 200]}"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_endpoint_not_rate_limited(app):
    """``/metrics`` (Prometheus scrape) sin limit."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        statuses = [(await ac.get("/metrics")).status_code for _ in range(30)]
    assert all(s == 200 for s in statuses)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_control_start_rate_limited_after_10(app):
    """``/v1/control/start`` permite 10/minute, devuelve 429 al 11º hit."""
    transport = ASGITransport(app=app)
    payload = {
        "config_path": "/tmp/x.yaml",
        "mode": "live",
        "aulas": 1,
        "faults": [],
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        statuses: list[int] = []
        for _ in range(12):
            r = await ac.post("/v1/control/start", json=payload)
            statuses.append(r.status_code)

    # Los primeros ~10 pueden ser 202 (acepta) o 409 (busy), pero ningún 429.
    # A partir del 11º deberíamos ver 429.
    initial = statuses[:10]
    assert all(s != 429 for s in initial), (
        f"Rate limit demasiado agresivo: 429 en los primeros 10 hits: {initial}"
    )
    later = statuses[10:]
    assert any(s == 429 for s in later), (
        f"No hubo 429 tras 10 hits/min: {statuses}"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_datasets_export_rate_limited_after_5(app):
    """``/v1/datasets/export`` permite 5/minute (más restrictivo: backfill caro)."""
    transport = ASGITransport(app=app)
    payload = {
        "months": 1,
        "format": "line_protocol",
        "include_faults": False,
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        statuses: list[int] = []
        for _ in range(7):
            r = await ac.post("/v1/datasets/export", json=payload)
            statuses.append(r.status_code)

    initial = statuses[:5]
    assert all(s != 429 for s in initial), (
        f"Rate limit demasiado agresivo: 429 en los primeros 5 hits: {initial}"
    )
    later = statuses[5:]
    assert any(s == 429 for s in later), (
        f"No hubo 429 tras 5 hits/min en /v1/datasets/export: {statuses}"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limit_429_response_shape(app):
    """Cuando se excede el límite, la response 429 tiene un body JSON identificable."""
    transport = ASGITransport(app=app)
    payload = {
        "config_path": "/tmp/x.yaml",
        "mode": "live",
        "aulas": 1,
        "faults": [],
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Disparar más de 10/minute.
        last_response = None
        for _ in range(15):
            last_response = await ac.post("/v1/control/start", json=payload)

    # La última debería ser 429 (Too Many Requests).
    assert last_response.status_code == 429, (
        f"Esperado 429 tras 15 hits, got {last_response.status_code}"
    )
    # Mensaje slowapi: "Rate limit exceeded: 10 per 1 minute"
    body_text = last_response.text
    assert "rate" in body_text.lower() or "limit" in body_text.lower(), (
        f"Body 429 sin mención a rate/limit: {body_text!r}"
    )
