"""E2E Caso A — pipeline IoT en vivo.

Requiere `task up` ejecutado y stack `healthy`. Verifica:
    1. /healthz responde 200.
    2. Trigger control/start mode=live → 202.
    3. Datos visibles en MQTT y/o Influx tras 60 s (no obligatorio aquí; se
       valida en tests Influx específicos).
"""

from __future__ import annotations

import time

import httpx
import pytest


@pytest.mark.smoke
@pytest.mark.slow
def test_generator_healthz(generator_url: str) -> None:
    r = httpx.get(f"{generator_url}/healthz", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


@pytest.mark.smoke
@pytest.mark.slow
def test_metrics_endpoint(generator_url: str) -> None:
    r = httpx.get(f"{generator_url}/metrics", timeout=5)
    assert r.status_code == 200
    assert b"captia_bms" in r.content or b"# HELP" in r.content


@pytest.mark.smoke
@pytest.mark.slow
def test_caseA_start_live_returns_202(generator_url: str, auth_headers: dict) -> None:
    r = httpx.post(
        f"{generator_url}/v1/control/start",
        json={
            "config_path": "/app/config/projects/bms_v1_demo.yaml",
            "mode": "live",
            "aulas": 5,
            "faults": [],
        },
        headers=auth_headers,
        timeout=10,
    )
    # Aceptamos 202 (nuevo job) o 409 (ya activo desde ejecución previa).
    assert r.status_code in (202, 409), f"unexpected: {r.status_code} {r.text}"
    if r.status_code == 202:
        assert "job_id" in r.json()
        # Limpiar
        job_id = r.json()["job_id"]
        time.sleep(1)
        httpx.post(
            f"{generator_url}/v1/control/stop?job_id={job_id}",
            headers=auth_headers,
            timeout=5,
        )
