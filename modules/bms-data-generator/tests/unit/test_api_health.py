import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_healthz(client) -> None:
    r = await client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "uptime" in body
    assert "version" in body


@pytest.mark.unit
@pytest.mark.asyncio
async def test_readyz_503_when_not_ready(client) -> None:
    r = await client.get("/readyz")
    # En arranque, mqtt_connected=False → 503
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "not_ready"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_metrics_endpoint(client) -> None:
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert b"captia_bms" in r.content or b"# HELP" in r.content
