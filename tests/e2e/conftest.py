"""Fixtures compartidas por tests E2E.

Estos tests requieren `task up` previo. Se marcan como `smoke` y `slow`.
"""

from __future__ import annotations

import os

import pytest


def _generator_url() -> str:
    port = os.environ.get("BMS_GENERATOR_PORT_HOST", "8120")
    return f"http://localhost:{port}"


def _influxdb_url() -> str:
    port = os.environ.get("INFLUXDB_PORT_HOST", "8087")
    return f"http://localhost:{port}"


def _grafana_url() -> str:
    port = os.environ.get("GRAFANA_PORT_HOST", "3001")
    return f"http://localhost:{port}"


@pytest.fixture
def generator_url() -> str:
    return _generator_url()


@pytest.fixture
def influxdb_url() -> str:
    return _influxdb_url()


@pytest.fixture
def grafana_url() -> str:
    return _grafana_url()


@pytest.fixture
def api_token() -> str:
    return os.environ.get("BMS_API_TOKEN", "")


@pytest.fixture
def auth_headers(api_token: str) -> dict:
    if not api_token:
        return {}
    return {"Authorization": f"Bearer {api_token}"}
