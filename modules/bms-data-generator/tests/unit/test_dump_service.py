"""Unit tests for :class:`DumpService` (factory mocked, threads disabled)."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from bms_data_generator.services.dump_service import DumpService


class _FakeRes:
    points_emitted = 0


def _fake_factory(job) -> list[_FakeRes]:
    # Simulate writing a tiny output file so size_bytes / sha256 are populated.
    job.output_path.write_text("# fake dump\n", encoding="utf-8")
    return [_FakeRes()]


@pytest.fixture
def existing_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "scenario.yaml"
    p.write_text("project: {}\n", encoding="utf-8")
    return p


@pytest.fixture
def service(tmp_path: Path) -> DumpService:
    s = DumpService(output_dir=tmp_path / "out", runner_factory=_fake_factory)
    return s


@pytest.mark.unit
def test_export_creates_job(service: DumpService, existing_yaml: Path) -> None:
    job_id, path = service.export(
        months=1,
        format="line_protocol",
        include_faults=False,
        config_path=str(existing_yaml),
    )
    assert job_id
    assert str(path).endswith(".lp")
    # Wait briefly for the daemon thread to settle.
    for _ in range(50):
        info = service.get(job_id)
        if info["status"] in {"done", "error"}:
            break
        threading.Event().wait(0.02)
    info = service.get(job_id)
    assert info["status"] == "done"
    assert info["size_bytes"] > 0
    assert info["sha256"] is not None


@pytest.mark.unit
def test_export_invalid_format_raises(service: DumpService) -> None:
    with pytest.raises(ValueError):
        service.export(months=1, format="parquet", include_faults=False)


@pytest.mark.unit
def test_export_invalid_months_raises(service: DumpService) -> None:
    with pytest.raises(ValueError):
        service.export(months=0, format="line_protocol", include_faults=False)
    with pytest.raises(ValueError):
        service.export(months=99, format="line_protocol", include_faults=False)


@pytest.mark.unit
def test_get_unknown_job_raises(service: DumpService) -> None:
    with pytest.raises(KeyError):
        service.get("unknown")


@pytest.mark.unit
def test_csv_format_has_correct_extension(service: DumpService, existing_yaml: Path) -> None:
    _job_id, path = service.export(
        months=1,
        format="csv_long",
        include_faults=False,
        config_path=str(existing_yaml),
    )
    assert str(path).endswith(".csv")


@pytest.mark.unit
def test_export_missing_config_marks_error(service: DumpService) -> None:
    job_id, _ = service.export(
        months=1,
        format="line_protocol",
        include_faults=False,
        config_path="/definitely/missing.yaml",
    )
    for _ in range(50):
        info = service.get(job_id)
        if info["status"] == "error":
            break
        threading.Event().wait(0.02)
    info = service.get(job_id)
    assert info["status"] == "error"
    assert "config not found" in (info["error"] or "")
