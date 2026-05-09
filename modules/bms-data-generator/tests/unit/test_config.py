import pytest

from bms_data_generator.config import Settings, get_settings, reset_settings_cache


@pytest.mark.unit
def test_default_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BMS_GENERATOR_PORT", raising=False)
    monkeypatch.delenv("BMS_PORT", raising=False)
    monkeypatch.delenv("BMS_N_AULAS", raising=False)
    monkeypatch.delenv("BMS_SEED", raising=False)
    s = Settings()
    assert s.host == "0.0.0.0"
    assert s.port == 8120
    assert s.domain_id == "bms_classrooms"
    assert s.seed == 42
    assert s.n_aulas == 10
    assert s.captia_site == "ies_simarro"


@pytest.mark.unit
def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BMS_PORT", "9000")
    monkeypatch.setenv("BMS_N_AULAS", "70")
    monkeypatch.setenv("BMS_SEED", "100")
    s = Settings()
    assert s.port == 9000
    assert s.n_aulas == 70
    assert s.seed == 100


@pytest.mark.unit
def test_get_settings_cached() -> None:
    reset_settings_cache()
    a = get_settings()
    b = get_settings()
    assert a is b
