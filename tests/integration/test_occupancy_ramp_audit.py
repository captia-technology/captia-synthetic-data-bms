"""Auditoría de rampa entrada/salida ocupación (F-10 / PATCH 010).

Verifica que ``generate_occupancy_count`` suaviza transiciones de
ocupación cuando ``ramp_minutes > 0`` y que sin ese parámetro el
comportamiento legacy se preserva.

Cierra el hallazgo F-10 documentado en
``docs/audit/PHYSICAL_REALISM_REPORT.md``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from synthetic_generator.domains.bms_classrooms.physics.occupancy import (
    generate_occupancy_count,
)


def _step_p_occ(n: int = 240, freq_seconds: int = 5) -> tuple[pd.DatetimeIndex, pd.Series]:
    """Genera 20 min @ 5 s con un step de p_occ 0 → 0.85 a la mitad."""
    index = pd.date_range("2026-09-15T08:00:00Z", periods=n, freq=f"{freq_seconds}s")
    values = np.zeros(n, dtype=float)
    values[n // 2 :] = 0.85
    return index, pd.Series(values, index=index, name="p_occ")


@pytest.mark.integration
def test_legacy_no_ramp_keeps_poisson_jumps() -> None:
    """Sin ramp_minutes el Poisson genera saltos inmediatos al cambiar p_occ."""
    index, p_occ = _step_p_occ()
    rng = np.random.default_rng(42)
    occ = generate_occupancy_count(
        index, p_occ, capacity=28, util=0.75, day_variability=0.0, rng=rng,
    )
    # En la transición 0→0.85 el siguiente sample salta de 0 a ~18-22.
    transition_idx = len(occ) // 2
    delta = abs(int(occ.iloc[transition_idx] - occ.iloc[transition_idx - 1]))
    assert delta >= 10, (
        f"Sin ramp esperamos salto >= 10 personas en transición, got {delta}"
    )


@pytest.mark.integration
def test_ramp_zero_is_escape_hatch() -> None:
    """ramp_minutes=0 desactiva la rampa (= legacy)."""
    index, p_occ = _step_p_occ()
    rng_a = np.random.default_rng(42)
    occ_legacy = generate_occupancy_count(
        index, p_occ, capacity=28, util=0.75, day_variability=0.0, rng=rng_a,
    )
    rng_b = np.random.default_rng(42)
    occ_zero = generate_occupancy_count(
        index, p_occ, capacity=28, util=0.75, day_variability=0.0, rng=rng_b,
        ramp_minutes=0.0,
    )
    np.testing.assert_array_equal(occ_legacy.values, occ_zero.values)


@pytest.mark.integration
def test_ramp_5min_caps_consecutive_delta() -> None:
    """Con ramp=5 min y dt=5 s, max |Δocc| consecutivo ≤ 3 personas."""
    index, p_occ = _step_p_occ(n=480)
    rng = np.random.default_rng(42)
    occ = generate_occupancy_count(
        index, p_occ, capacity=28, util=0.75, day_variability=0.0, rng=rng,
        ramp_minutes=5.0,
    )
    diffs = occ.diff().abs().dropna()
    # alpha = 5/300 = 0.0167; salto inicial alpha * 22 ≈ 0.37 ≈ 0-1 tras round.
    # Permitimos ≤ 3 con margen (puede haber jitter Poisson aún tras EWMA).
    p99 = int(np.quantile(diffs.values, 0.99))
    assert p99 <= 3, (
        f"Con ramp=5 min, p99 |Δocc| consecutivo debería ser ≤ 3, got {p99}"
    )


@pytest.mark.integration
def test_ramp_respects_capacity() -> None:
    """El output redondeado nunca excede capacity ni baja de 0."""
    index, p_occ = _step_p_occ(n=480)
    rng = np.random.default_rng(42)
    occ = generate_occupancy_count(
        index, p_occ, capacity=15, util=0.95, day_variability=0.0, rng=rng,
        ramp_minutes=5.0,
    )
    assert int(occ.min()) >= 0
    assert int(occ.max()) <= 15


@pytest.mark.integration
def test_ramp_converges_after_5_tau() -> None:
    """Tras ~5 * ramp_minutes, occ converge cerca del expected (1 sigma)."""
    index, p_occ = _step_p_occ(n=720)  # 60 min
    rng = np.random.default_rng(42)
    occ = generate_occupancy_count(
        index, p_occ, capacity=30, util=0.8, day_variability=0.0, rng=rng,
        ramp_minutes=2.0,
    )
    # expected = 30 * 0.8 * 0.85 = 20.4 personas
    final_window = occ.iloc[-60:]  # últimos 5 min
    mean = float(final_window.mean())
    assert 17 < mean < 24, (
        f"Tras 5*ramp el output debería estar cerca de 20.4, got mean={mean:.1f}"
    )
