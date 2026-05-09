"""E2E Caso D — calidad aire 1min, 3 meses.

Requiere `task up`. Verifica que el endpoint acepta config caseD y que el
job se registra correctamente.
"""

from __future__ import annotations

import httpx
import pytest


@pytest.mark.smoke
@pytest.mark.slow
def test_caseD_export_3_months_iaq(generator_url: str, auth_headers: dict) -> None:
    r = httpx.post(
        f"{generator_url}/v1/datasets/export",
        json={
            "months": 3,
            "format": "csv_long",
            "include_faults": False,
            "config_path": "/app/config/projects/bms_v1_caseD_iaq.yaml",
        },
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 202, f"{r.status_code} {r.text}"
    body = r.json()
    assert body["output_path"].endswith(".csv")
