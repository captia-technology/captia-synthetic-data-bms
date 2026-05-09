"""E2E Caso B — dump export 1 mes (versión rápida del 12m).

Requiere `task up`. Verifica que el endpoint POST /v1/datasets/export devuelve
un job_id válido y que el GET del job devuelve estado válido.
"""

from __future__ import annotations

import httpx
import pytest


@pytest.mark.smoke
@pytest.mark.slow
def test_dump_export_returns_job_id(generator_url: str, auth_headers: dict) -> None:
    r = httpx.post(
        f"{generator_url}/v1/datasets/export",
        json={
            "months": 1,
            "format": "line_protocol",
            "include_faults": False,
            "config_path": "/app/config/projects/bms_v1_caseB_consumption.yaml",
        },
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 202, f"{r.status_code} {r.text}"
    body = r.json()
    assert "job_id" in body
    assert body["output_path"].endswith(".lp")


@pytest.mark.smoke
@pytest.mark.slow
def test_dump_get_job_status(generator_url: str, auth_headers: dict) -> None:
    r = httpx.post(
        f"{generator_url}/v1/datasets/export",
        json={"months": 1, "format": "line_protocol", "include_faults": False},
        headers=auth_headers,
        timeout=10,
    )
    job_id = r.json()["job_id"]
    s = httpx.get(f"{generator_url}/v1/datasets/jobs/{job_id}", headers=auth_headers, timeout=5)
    assert s.status_code == 200
    body = s.json()
    assert body["job_id"] == job_id
    assert body["status"] in {"in_progress", "done", "error"}
