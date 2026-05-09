"""Auditoría del rate limiter de la válvula (F-7 / PATCH 007).

Verifica que ``heating_valve_position`` aplica un slew-rate clamp cuando
``cfg_indoor.valve_max_rate_per_min`` > 0, y que sin ese parámetro el
comportamiento legacy se preserva.

Cierra el hallazgo F-7 documentado en
``docs/audit/PHYSICAL_REALISM_REPORT.md`` y la regla R-VLV-02 documentada
en ``docs/specs/digital-twin-bms-physics-validation/04-physical-plausibility-rules.md``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from synthetic_generator.domains.bms_classrooms.physics.actuators import (
    _enforce_rate_limit,
    heating_valve_position,
)


def _make_step_inputs(n: int = 240, freq_seconds: int = 5):
    """Setpoint constante 21 °C y temperatura interior con escalón violento.

    Provoca err: 0 → 5 °C → 0 → -5 °C, lo que sin limiter genera saltos
    0 → 100 → 0 → 0 % entre samples.
    """
    index = pd.date_range("2026-05-09T08:00:00Z", periods=n, freq=f"{freq_seconds}s")
    setp = pd.Series([21.0] * n, index=index, name="setpoint")
    indoor_vals = np.full(n, 21.0)
    indoor_vals[n // 4 : n // 2] = 16.0   # err = +5
    indoor_vals[n // 2 : 3 * n // 4] = 26.0  # err = -5
    indoor = pd.Series(indoor_vals, index=index, name="indoor")
    mode = pd.Series(["heat"] * n, index=index, name="hvac_mode")
    return index, indoor, setp, mode


@pytest.mark.integration
def test_legacy_signature_preserved() -> None:
    """Sin cfg_indoor el comportamiento legacy se preserva (no rate limit)."""
    _, indoor, setp, mode = _make_step_inputs()
    out = heating_valve_position(indoor, setp, mode)
    assert isinstance(out, pd.Series)
    # Salida puede tener saltos grandes — eso es exactamente el comportamiento legacy.
    diffs = out.diff().abs().dropna()
    assert diffs.max() > 50.0, "Legacy: la válvula debe poder saltar >50 % en un sample"


@pytest.mark.integration
def test_rate_zero_is_escape_hatch() -> None:
    """Con valve_max_rate_per_min=0 el post-process no toca nada."""
    _, indoor, setp, mode = _make_step_inputs()
    out_legacy = heating_valve_position(indoor, setp, mode)
    out_zero = heating_valve_position(
        indoor, setp, mode,
        cfg_indoor={"valve_max_rate_per_min": 0.0},
    )
    np.testing.assert_array_equal(out_legacy.values, out_zero.values)


@pytest.mark.integration
def test_rate_limiter_caps_consecutive_delta() -> None:
    """Con max_rate=60 %/min y dt=5 s (=0.0833 min), el max step es 5 %."""
    _, indoor, setp, mode = _make_step_inputs()
    out = heating_valve_position(
        indoor, setp, mode,
        cfg_indoor={"valve_max_rate_per_min": 60.0},
    )
    diffs = out.diff().abs().dropna()
    max_step = 60.0 * (5.0 / 60.0)  # = 5.0
    # Toleramos pequeño float epsilon.
    assert float(diffs.max()) <= max_step + 1e-6, (
        f"Rate limiter falla: max |Δpos| consecutivo = {diffs.max():.3f} "
        f"(esperado ≤ {max_step:.3f})"
    )


@pytest.mark.integration
def test_rate_limiter_handles_edge_cases() -> None:
    """Edge cases: serie 1 sample, serie todo 0."""
    out = _enforce_rate_limit(np.array([42.0]), dt_min=1.0, max_rate_per_min=60.0)
    assert out.tolist() == [42.0]
    arr = np.zeros(20, dtype=float)
    np.testing.assert_array_equal(_enforce_rate_limit(arr, 1.0, 60.0), arr)


@pytest.mark.integration
def test_rate_limiter_is_symmetric() -> None:
    """Limita igual subidas y bajadas."""
    arr = np.array([0.0, 100.0, 0.0, 100.0])
    out = _enforce_rate_limit(arr, dt_min=1.0, max_rate_per_min=10.0)
    # Subidas/bajadas deberían ser ≤ 10 cada paso.
    diffs = np.diff(out)
    assert (np.abs(diffs) <= 10.0 + 1e-6).all()
    # Y debería seguir el signo de la dirección.
    assert out[1] > out[0]
    assert out[2] < out[1]
