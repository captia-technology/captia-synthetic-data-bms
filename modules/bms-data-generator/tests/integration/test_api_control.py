import pytest

from bms_data_generator.config import reset_settings_cache


@pytest.mark.integration
@pytest.mark.asyncio
async def test_control_start_no_token_when_unset(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    reset_settings_cache()
    r = await client.post(
        "/v1/control/start",
        json={"config_path": "/tmp/x.yaml", "mode": "live", "aulas": 1, "faults": []},
    )
    assert r.status_code == 202
    assert "job_id" in r.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_control_start_requires_token_when_set(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "secret")
    reset_settings_cache()
    r = await client.post(
        "/v1/control/start",
        json={"config_path": "/tmp/x.yaml", "mode": "live", "aulas": 1, "faults": []},
    )
    assert r.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_control_start_with_valid_token(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "secret")
    reset_settings_cache()
    r = await client.post(
        "/v1/control/start",
        json={"config_path": "/tmp/x.yaml", "mode": "live", "aulas": 1, "faults": []},
        headers={"Authorization": "Bearer secret"},
    )
    assert r.status_code == 202
    assert "job_id" in r.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_control_invalid_mode_returns_400(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    reset_settings_cache()
    r = await client.post(
        "/v1/control/start",
        json={"config_path": "/tmp/x.yaml", "mode": "wrong", "aulas": 1, "faults": []},
    )
    assert r.status_code == 422  # Pydantic validation


@pytest.mark.integration
@pytest.mark.asyncio
async def test_control_invalid_fault_returns_400(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    reset_settings_cache()
    r = await client.post(
        "/v1/control/start",
        json={
            "config_path": "/tmp/x.yaml",
            "mode": "live",
            "aulas": 1,
            "faults": ["unknown_fault"],
        },
    )
    assert r.status_code == 400


@pytest.mark.integration
@pytest.mark.asyncio
async def test_control_concurrent_start_returns_409(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    reset_settings_cache()
    body = {"config_path": "/tmp/x.yaml", "mode": "live", "aulas": 1, "faults": []}
    r1 = await client.post("/v1/control/start", json=body)
    assert r1.status_code == 202
    r2 = await client.post("/v1/control/start", json=body)
    assert r2.status_code == 409


@pytest.mark.integration
@pytest.mark.asyncio
async def test_control_status_returns_idle_initially(client) -> None:
    r = await client.get("/v1/control/status")
    assert r.status_code == 200
    assert r.json()["phase"] == "idle"
