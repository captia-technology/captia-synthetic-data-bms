"""Integration tests for /v1/query (no real InfluxDB; httpx is mocked)."""

from __future__ import annotations

import pytest

from bms_data_generator.config import reset_settings_cache


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_validation_missing_variable_returns_422(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    reset_settings_cache()
    r = await client.post("/v1/query", json={"start": "-1h"})
    assert r.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_unsafe_variable_returns_400(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    monkeypatch.setenv("INFLUXDB_TOKEN", "dummy")
    reset_settings_cache()
    r = await client.post(
        "/v1/query",
        json={"variable": 'co2"; drop bucket', "start": "-1h"},
    )
    assert r.status_code == 400
    body = r.json()
    assert body["detail"]["error"] == "validation_failed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_no_token_returns_503(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    monkeypatch.delenv("INFLUXDB_TOKEN", raising=False)
    reset_settings_cache()
    r = await client.post("/v1/query", json={"variable": "co2", "start": "-1h"})
    assert r.status_code == 503
    body = r.json()
    assert body["detail"]["error"] == "not_configured"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_with_mocked_influx_returns_rows(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    monkeypatch.setenv("INFLUXDB_TOKEN", "dummy-token")
    monkeypatch.setenv("INFLUXDB_URL", "http://test-influx:8086")
    monkeypatch.setenv("INFLUXDB_ORG", "captia")
    reset_settings_cache()

    fake_csv = (
        "#datatype,string,long,dateTime:RFC3339,double,string,string\n"
        ",result,table,_time,_value,asset_id,variable\n"
        ",_result,0,2026-05-09T12:00:00Z,712.3,AULA01,co2\n"
        ",_result,0,2026-05-09T12:00:05Z,713.1,AULA01,co2\n"
    )

    class _FakeResponse:
        status_code = 200
        text = fake_csv

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            return _FakeResponse()

    monkeypatch.setattr(
        "bms_data_generator.services.query_service.httpx.AsyncClient",
        _FakeAsyncClient,
    )

    r = await client.post(
        "/v1/query",
        json={"variable": "co2", "asset_id": "AULA01", "start": "-30m"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["bucket"] == "telemetry"
    assert len(body["rows"]) == 2
    assert body["rows"][0]["asset_id"] == "AULA01"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_long_window_picks_1h_bucket(client, monkeypatch) -> None:
    monkeypatch.setenv("BMS_API_TOKEN", "")
    monkeypatch.setenv("INFLUXDB_TOKEN", "dummy")
    reset_settings_cache()

    class _FakeResponse:
        status_code = 200
        text = ",result,table,_time,_value,asset_id,variable\n"

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            return _FakeResponse()

    monkeypatch.setattr(
        "bms_data_generator.services.query_service.httpx.AsyncClient",
        _FakeAsyncClient,
    )

    r = await client.post(
        "/v1/query",
        json={"variable": "power_01", "start": "-30d", "aggregation": "max"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["bucket"] == "telemetry_1h"
    assert 'r.stat == "max"' in body["flux"]
