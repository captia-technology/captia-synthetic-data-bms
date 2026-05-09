import pytest

from bms_calibration.physics_overrides import (
    co2_rise_rate_per_person_per_min,
    get_overrides,
    hvac_response_time_minutes,
    temp_outdoor_indoor_coupling,
)


@pytest.mark.unit
def test_default_hooks_return_none() -> None:
    assert co2_rise_rate_per_person_per_min() is None
    assert hvac_response_time_minutes() is None
    assert temp_outdoor_indoor_coupling() is None


@pytest.mark.unit
def test_get_overrides_empty_when_no_hooks_set() -> None:
    assert get_overrides() == {}
