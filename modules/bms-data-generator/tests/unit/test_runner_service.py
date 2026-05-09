import pytest

from bms_data_generator.services.runner_service import RunnerService


@pytest.fixture
def service() -> RunnerService:
    return RunnerService()


@pytest.mark.unit
def test_start_creates_job(service: RunnerService) -> None:
    job_id = service.start(config_path="/tmp/x.yaml", mode="live", aulas=10, faults=[])
    assert job_id
    st = service.status(job_id)
    assert st["job_id"] == job_id
    assert st["phase"] in {"pending", "running", "live"}


@pytest.mark.unit
def test_stop_unknown_job_raises(service: RunnerService) -> None:
    with pytest.raises(KeyError):
        service.stop("unknown")


@pytest.mark.unit
def test_concurrent_start_raises_when_busy(service: RunnerService) -> None:
    service.start(config_path="/tmp/x.yaml", mode="live", aulas=10, faults=[])
    with pytest.raises(RuntimeError, match="busy"):
        service.start(config_path="/tmp/y.yaml", mode="live", aulas=10, faults=[])


@pytest.mark.unit
def test_status_idle_when_no_jobs(service: RunnerService) -> None:
    assert service.status()["phase"] == "idle"


@pytest.mark.unit
def test_stop_releases_active_slot(service: RunnerService) -> None:
    job_id = service.start(config_path="/tmp/x.yaml", mode="live", aulas=10, faults=[])
    service.stop(job_id)
    new_job = service.start(config_path="/tmp/y.yaml", mode="backfill", aulas=5, faults=[])
    assert new_job != job_id
