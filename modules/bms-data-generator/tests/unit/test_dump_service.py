from pathlib import Path

import pytest

from bms_data_generator.services.dump_service import DumpService


@pytest.fixture
def service(tmp_path: Path) -> DumpService:
    return DumpService(output_dir=tmp_path)


@pytest.mark.unit
def test_export_creates_job(service: DumpService) -> None:
    job_id, path = service.export(months=1, format="line_protocol", include_faults=False)
    assert job_id
    assert str(path).endswith(".lp")
    info = service.get(job_id)
    assert info["status"] == "in_progress"


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
def test_csv_format_has_correct_extension(service: DumpService) -> None:
    _job_id, path = service.export(months=1, format="csv_long", include_faults=False)
    assert str(path).endswith(".csv")
