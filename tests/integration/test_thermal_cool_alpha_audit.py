"""Auditoría de bifurcación α cool vs heat en thermal model (F-5 / PATCH 008).

Verifica que ``simulate_indoor_temperature`` usa una constante de tiempo
más corta cuando ``hvac_mode == "cool"``, y que sin el parámetro el
comportamiento legacy se preserva.

Cierra el hallazgo F-5 documentado en
``docs/audit/PHYSICAL_REALISM_REPORT.md``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from synthetic_generator.domains.bms_classrooms.physics.indoor import (
    simulate_indoor_temperature,
)


def _make_inputs(n: int = 720, freq_seconds: int = 5):
    """1 h @ 5 s con outdoor=28 °C, occ=0, setpoint=22 °C, HVAC ON."""
    index = pd.date_range("2026-07-15T13:00:00Z", periods=n, freq=f"{freq_seconds}s")
    outdoor = pd.Series([28.0] * n, index=index, name="outdoor")
    occ = pd.Series([0] * n, index=index, name="occ")
    setp = pd.Series([22.0] * n, index=index, name="setpoint")
    enable = pd.Series([1] * n, index=index, name="hvac_enable")
    return index, outdoor, occ, setp, enable


@pytest.mark.integration
def test_legacy_signature_preserved() -> None:
    """Sin hvac_mode el comportamiento legacy se preserva."""
    index, outdoor, occ, setp, enable = _make_inputs()
    rng = np.random.default_rng(42)
    out = simulate_indoor_temperature(
        index, outdoor, occ, setp, enable,
        cfg_indoor={"tau_minutes": 90, "initial_temp": 28.0,
                    "occupancy_heat_gain_c_per_person": 0.02},
        rng=rng,
    )
    assert isinstance(out, pd.Series)
    assert len(out) == len(index)


@pytest.mark.integration
def test_tau_cool_equal_tau_is_escape_hatch() -> None:
    """Con tau_cool_minutes==tau_minutes el output es idéntico al legacy."""
    index, outdoor, occ, setp, enable = _make_inputs()
    mode = pd.Series(["cool"] * len(index), index=index, name="hvac_mode")
    cfg = {
        "tau_minutes": 90,
        "tau_cool_minutes": 90,  # mismo
        "initial_temp": 28.0,
        "occupancy_heat_gain_c_per_person": 0.02,
    }
    rng_a = np.random.default_rng(42)
    out_with_mode = simulate_indoor_temperature(
        index, outdoor, occ, setp, enable, cfg, rng_a, hvac_mode=mode,
    )
    rng_b = np.random.default_rng(42)
    out_legacy = simulate_indoor_temperature(
        index, outdoor, occ, setp, enable, cfg, rng_b,
    )
    np.testing.assert_array_almost_equal(out_with_mode.values, out_legacy.values)


@pytest.mark.integration
def test_cool_reaches_setpoint_faster_than_heat() -> None:
    """Con tau_cool < tau, cooling alcanza el setpoint más rápido."""
    index, outdoor, occ, setp, enable = _make_inputs(n=1440)  # 2 h
    mode_cool = pd.Series(["cool"] * len(index), index=index, name="hvac_mode")
    mode_heat = pd.Series(["heat"] * len(index), index=index, name="hvac_mode")
    cfg = {
        "tau_minutes": 90,
        "tau_cool_minutes": 30,  # 3× más rápido que heat
        "initial_temp": 28.0,
        "occupancy_heat_gain_c_per_person": 0.02,
    }
    rng_cool = np.random.default_rng(42)
    out_cool = simulate_indoor_temperature(
        index, outdoor, occ, setp, enable, cfg, rng_cool, hvac_mode=mode_cool,
    )
    rng_heat = np.random.default_rng(42)
    out_heat = simulate_indoor_temperature(
        index, outdoor, occ, setp, enable, cfg, rng_heat, hvac_mode=mode_heat,
    )
    # Tras 30 min (360 samples), cool debería estar más cerca del setpoint que heat.
    idx_30min = 360
    err_cool = abs(float(out_cool.iloc[idx_30min] - 22.0))
    err_heat = abs(float(out_heat.iloc[idx_30min] - 22.0))
    assert err_cool < err_heat * 0.6, (
        f"Cooling debería ser ≥ 1.7× más rápido al setpoint: "
        f"err_cool={err_cool:.2f} vs err_heat={err_heat:.2f} a 30 min"
    )


@pytest.mark.integration
def test_heat_mode_uses_tau_heat() -> None:
    """Con hvac_mode='heat' usa tau_minutes, no tau_cool_minutes."""
    index, outdoor, occ, setp, enable = _make_inputs(n=1440)
    mode_heat = pd.Series(["heat"] * len(index), index=index, name="hvac_mode")
    cfg_with_cool_short = {
        "tau_minutes": 90,
        "tau_cool_minutes": 10,  # cool muy rápido pero no aplica
        "initial_temp": 28.0,
        "occupancy_heat_gain_c_per_person": 0.02,
    }
    cfg_no_cool = {
        "tau_minutes": 90,
        "initial_temp": 28.0,
        "occupancy_heat_gain_c_per_person": 0.02,
    }
    rng_a = np.random.default_rng(42)
    out_with_short_cool = simulate_indoor_temperature(
        index, outdoor, occ, setp, enable, cfg_with_cool_short, rng_a, hvac_mode=mode_heat,
    )
    rng_b = np.random.default_rng(42)
    out_legacy = simulate_indoor_temperature(
        index, outdoor, occ, setp, enable, cfg_no_cool, rng_b, hvac_mode=mode_heat,
    )
    # En modo heat, ambos deberían dar lo mismo (tau_cool_minutes ignorado).
    np.testing.assert_array_almost_equal(
        out_with_short_cool.values, out_legacy.values, decimal=4,
    )
