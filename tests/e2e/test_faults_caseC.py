"""E2E Caso C — fault injection.

Requiere `task up`. Verifica que el control/start con `faults` no vacío es
aceptado por el endpoint. La ejecución completa de fault injection se valida
en tests integration de `bms_calibration`.
"""

from __future__ import annotations

import httpx
import pytest


@pytest.mark.smoke
@pytest.mark.slow
def test_caseC_start_with_4_fault_types(generator_url: str, auth_headers: dict) -> None:
    r = httpx.post(
        f"{generator_url}/v1/control/start",
        json={
            "config_path": "/app/config/projects/bms_v1_caseC_faults.yaml",
            "mode": "backfill",
            "aulas": 3,
            "faults": ["sensor_drift", "valve_stuck", "fan_failure", "refrigerant_low"],
        },
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code in (202, 409), f"{r.status_code} {r.text}"


@pytest.mark.smoke
@pytest.mark.slow
def test_caseC_invalid_fault_type_returns_400(generator_url: str, auth_headers: dict) -> None:
    r = httpx.post(
        f"{generator_url}/v1/control/start",
        json={
            "config_path": "/app/config/projects/bms_v1_caseC_faults.yaml",
            "mode": "backfill",
            "aulas": 3,
            "faults": ["unknown_fault"],
        },
        headers=auth_headers,
        timeout=10,
    )
    assert r.status_code == 400
