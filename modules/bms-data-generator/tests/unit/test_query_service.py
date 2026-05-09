"""Unit tests for the read-path service (bucket selector + Flux builder)."""

from __future__ import annotations

import pytest

from bms_data_generator.services.query_service import (
    QueryRequest,
    _parse_csv,
    build_flux,
    select_bucket,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "start, expected_bucket, expected_rollup",
    [
        ("-30m", "telemetry", False),
        ("-1h", "telemetry", False),
        ("-2h", "telemetry_1m", True),
        ("-23h", "telemetry_1m", True),
        ("-1d", "telemetry_1m", True),
        ("-2d", "telemetry_15m", True),
        ("-7d", "telemetry_15m", True),
        ("-30d", "telemetry_1h", True),
        ("-180d", "telemetry_1h", True),
        ("-365d", "telemetry_1h", True),
        ("-2y", "telemetry_1h", True),  # invalid unit -> falls back to absolute path
        ("2026-05-01T00:00:00Z", "telemetry_1h", True),  # absolute -> long-window default
    ],
)
def test_select_bucket_matches_centinela_table(
    start: str, expected_bucket: str, expected_rollup: bool
) -> None:
    bucket, is_rollup = select_bucket(start)
    assert bucket == expected_bucket
    assert is_rollup is expected_rollup


@pytest.mark.unit
def test_build_flux_raw_path_includes_aggregateWindow() -> None:
    req = QueryRequest(variable="co2", start="-30m", aggregation="mean")
    flux = build_flux(req, bucket="telemetry", is_rollup=False)
    assert 'from(bucket: "telemetry")' in flux
    assert 'r._measurement == "captia_point"' in flux
    assert 'r.variable == "co2"' in flux
    assert "aggregateWindow(every: 1m, fn: mean" in flux


@pytest.mark.unit
def test_build_flux_rollup_path_filters_by_stat() -> None:
    req = QueryRequest(variable="power_01", start="-7d", aggregation="max")
    flux = build_flux(req, bucket="telemetry_15m", is_rollup=True)
    assert 'r.stat == "max"' in flux
    assert "aggregateWindow" not in flux


@pytest.mark.unit
def test_build_flux_includes_asset_filter_when_provided() -> None:
    req = QueryRequest(variable="co2", asset_id="AULA01")
    flux = build_flux(req, bucket="telemetry", is_rollup=False)
    assert 'r.asset_id == "AULA01"' in flux


@pytest.mark.unit
def test_build_flux_rejects_unsafe_variable() -> None:
    req = QueryRequest(variable='co2"; drop bucket')
    with pytest.raises(ValueError, match="unsafe"):
        build_flux(req, bucket="telemetry", is_rollup=False)


@pytest.mark.unit
def test_build_flux_rejects_unknown_aggregation() -> None:
    req = QueryRequest(variable="co2", aggregation="median")
    with pytest.raises(ValueError, match="unsupported aggregation"):
        build_flux(req, bucket="telemetry", is_rollup=False)


@pytest.mark.unit
def test_parse_csv_strips_bookkeeping_columns() -> None:
    csv = (
        "#datatype,string,long,dateTime:RFC3339,double,string,string\n"
        "#group,false,false,false,false,true,true\n"
        ",result,table,_time,_value,asset_id,variable\n"
        ",_result,0,2026-05-09T12:00:00Z,712.3,AULA01,co2\n"
        ",_result,0,2026-05-09T12:00:05Z,713.1,AULA01,co2\n"
    )
    rows = _parse_csv(csv)
    assert len(rows) == 2
    assert rows[0]["_time"] == "2026-05-09T12:00:00Z"
    assert rows[0]["_value"] == "712.3"
    assert rows[0]["asset_id"] == "AULA01"
    assert rows[0]["variable"] == "co2"
    # Bookkeeping columns must NOT leak.
    assert "result" not in rows[0]
    assert "table" not in rows[0]


@pytest.mark.unit
def test_parse_csv_empty_returns_empty_list() -> None:
    assert _parse_csv("") == []
    assert _parse_csv("# only comments\n# nothing else\n") == []
