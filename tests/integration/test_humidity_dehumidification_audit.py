"""Auditoría de humidity dehumidification en cooling (L-PV-09 / PATCH 003).

Verifica que ``simulate_humidity`` aplica deshumidificación cuando HVAC está
en cooling mode, y que sin esos parámetros el comportamiento legacy se
preserva.

Cierra el hallazgo F-1 documentado en ``docs/audit/PHYSICAL_REALISM_REPORT.md``
y la regla R-RH-02 documentada en
``docs/specs/digital-twin-bms-physics-validation/04-physical-plausibility-rules.md``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from synthetic_generator.domains.bms_classrooms.physics.indoor import (
    simulate_humidity,
)


@pytest.fixture
def long_run() -> tuple[pd.DatetimeIndex, pd.Series, pd.Series]:
    """720 samples (~1 h @ 5 s) con outdoor 28 °C y ocupación 15 personas."""
    index = pd.date_range("2026-07-15T10:00:00Z", periods=720, freq="5s")
    outdoor = pd.Series([28.0] * len(index), index=index, name="outdoor_temp")
    occ = pd.Series([15] * len(index), index=index, name="occupancy")
    return index, outdoor, occ


@pytest.mark.integration
def test_legacy_signature_preserved(long_run) -> None:
    """Sin hvac_enable/mode, comportamiento legacy se preserva (signature back-compat)."""
    index, outdoor, occ = long_run
    rng = np.random.default_rng(42)
    h = simulate_humidity(
        index, outdoor, occ,
        cfg_h={"outdoor_mean": 55.0, "occupancy_gain_per_person": 0.08},
        rng=rng,
    )
    # Legacy: humidity drift toward outdoor_mean + 0.08 * 15 = 56.2 %RH
    assert 50.0 < float(h.mean()) < 60.0, (
        f"Legacy humidity model fuera de rango esperado: mean {h.mean():.2f}"
    )


@pytest.mark.integration
def test_cooling_lowers_humidity_vs_no_hvac(long_run) -> None:
    """Cooling pull RH abajo respecto al baseline sin HVAC."""
    index, outdoor, occ = long_run
    enable_off = pd.Series([0] * len(index), index=index, name="hvac_enable")
    mode_off = pd.Series(["off"] * len(index), index=index, name="hvac_mode")
    enable_cool = pd.Series([1] * len(index), index=index, name="hvac_enable")
    mode_cool = pd.Series(["cool"] * len(index), index=index, name="hvac_mode")

    cfg = {
        "outdoor_mean": 55.0,
        "occupancy_gain_per_person": 0.08,
        "tau_minutes": 30,            # tau corto para que el efecto se vea en 1 h
        "cooling_dehum_delta": 8.0,
    }

    rng_a = np.random.default_rng(42)
    h_off = simulate_humidity(index, outdoor, occ, cfg, rng_a, enable_off, mode_off)

    rng_b = np.random.default_rng(42)
    h_cool = simulate_humidity(index, outdoor, occ, cfg, rng_b, enable_cool, mode_cool)

    delta = float(h_off.iloc[-1] - h_cool.iloc[-1])
    assert delta >= 5.0, (
        f"Cooling no deshumidifica suficiente: Δ={delta:.2f} %RH "
        f"(esperado ≥ 5 %RH; off={h_off.iloc[-1]:.2f}, cool={h_cool.iloc[-1]:.2f})"
    )


@pytest.mark.integration
def test_heating_does_not_dehumidify(long_run) -> None:
    """Heating no debe aplicar dehum (modo ≠ cool)."""
    index, outdoor, occ = long_run
    enable = pd.Series([1] * len(index), index=index, name="hvac_enable")
    mode_heat = pd.Series(["heat"] * len(index), index=index, name="hvac_mode")
    mode_off = pd.Series(["off"] * len(index), index=index, name="hvac_mode")

    cfg = {
        "outdoor_mean": 55.0,
        "occupancy_gain_per_person": 0.08,
        "tau_minutes": 30,
        "cooling_dehum_delta": 8.0,
    }

    rng_a = np.random.default_rng(42)
    h_heat = simulate_humidity(index, outdoor, occ, cfg, rng_a, enable, mode_heat)

    enable_off = pd.Series([0] * len(index), index=index, name="hvac_enable")
    rng_b = np.random.default_rng(42)
    h_off = simulate_humidity(index, outdoor, occ, cfg, rng_b, enable_off, mode_off)

    delta = abs(float(h_heat.iloc[-1] - h_off.iloc[-1]))
    assert delta < 1.0, (
        f"Heating no debería afectar humidity: Δ={delta:.2f} %RH (esperado ≈ 0)"
    )


@pytest.mark.integration
def test_tau_minutes_configurable(long_run) -> None:
    """``tau_minutes`` realmente cambia la velocidad de respuesta."""
    index, outdoor, occ = long_run
    rng_a = np.random.default_rng(42)
    h_fast = simulate_humidity(
        index, outdoor, occ,
        cfg_h={"outdoor_mean": 55.0, "occupancy_gain_per_person": 0.08, "tau_minutes": 10},
        rng=rng_a,
    )
    rng_b = np.random.default_rng(42)
    h_slow = simulate_humidity(
        index, outdoor, occ,
        cfg_h={"outdoor_mean": 55.0, "occupancy_gain_per_person": 0.08, "tau_minutes": 600},
        rng=rng_b,
    )
    # Con tau corto, alcanza al asintote (≈56.2) más rápido. Con tau largo, se queda cerca del inicial (~55).
    final_fast = float(h_fast.iloc[-1])
    final_slow = float(h_slow.iloc[-1])
    # tau corto debería estar más cerca del target, tau largo más cerca del inicial.
    # Solo verificamos que son significativamente distintos.
    assert abs(final_fast - final_slow) > 0.3, (
        f"tau_minutes no parece afectar dinámica: fast={final_fast:.2f}, slow={final_slow:.2f}"
    )


@pytest.mark.integration
def test_cooling_dehum_delta_zero_disables(long_run) -> None:
    """Con ``cooling_dehum_delta=0``, cooling no deshumidifica (escape hatch)."""
    index, outdoor, occ = long_run
    enable = pd.Series([1] * len(index), index=index, name="hvac_enable")
    mode_cool = pd.Series(["cool"] * len(index), index=index, name="hvac_mode")
    mode_off = pd.Series(["off"] * len(index), index=index, name="hvac_mode")
    enable_off = pd.Series([0] * len(index), index=index, name="hvac_enable")

    cfg = {
        "outdoor_mean": 55.0,
        "occupancy_gain_per_person": 0.08,
        "tau_minutes": 30,
        "cooling_dehum_delta": 0.0,   # escape hatch
    }

    rng_a = np.random.default_rng(42)
    h_cool = simulate_humidity(index, outdoor, occ, cfg, rng_a, enable, mode_cool)

    rng_b = np.random.default_rng(42)
    h_off = simulate_humidity(index, outdoor, occ, cfg, rng_b, enable_off, mode_off)

    delta = abs(float(h_cool.iloc[-1] - h_off.iloc[-1]))
    assert delta < 0.5, (
        f"Con dehum_delta=0 el cooling no debería afectar: Δ={delta:.2f} %RH"
    )
