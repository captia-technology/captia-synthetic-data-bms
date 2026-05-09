import threading

import pytest

from bms_data_generator.config import reset_settings_cache


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_creates_job(client, monkeypatch, existing_yaml) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    reset_settings_cache()
    r = await client.post(
        "/v1/datasets/export",
        json={
            "months": 1,
            "format": "line_protocol",
            "include_faults": False,
            "config_path": str(existing_yaml),
        },
    )
    assert r.status_code == 202
    body = r.json()
    assert "job_id" in body
    assert body["output_path"].endswith(".lp")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_invalid_format_returns_422(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    reset_settings_cache()
    r = await client.post(
        "/v1/datasets/export",
        json={"months": 1, "format": "parquet", "include_faults": False},
    )
    assert r.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_job_reaches_done_with_fake_factory(client, monkeypatch, existing_yaml) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    reset_settings_cache()
    create = await client.post(
        "/v1/datasets/export",
        json={
            "months": 1,
            "format": "csv_long",
            "include_faults": True,
            "config_path": str(existing_yaml),
        },
    )
    job_id = create.json()["job_id"]

    final_status = None
    for _ in range(50):
        r = await client.get(f"/v1/datasets/jobs/{job_id}")
        assert r.status_code == 200
        final_status = r.json()["status"]
        if final_status in {"done", "error"}:
            break
        threading.Event().wait(0.02)
    assert final_status == "done"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_job_unknown_returns_404(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    reset_settings_cache()
    r = await client.get("/v1/datasets/jobs/nonexistent")
    assert r.status_code == 404
