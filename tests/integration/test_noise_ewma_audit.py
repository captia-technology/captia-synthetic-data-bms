"""Auditoría de EWMA en `simulate_noise` (F-6 / PATCH 009).

Verifica que ``simulate_noise`` suaviza transiciones de ocupación cuando
``cfg_noise.tau_minutes`` > 0 y que sin esa clave el comportamiento legacy
se preserva.

Cierra el hallazgo F-6 documentado en
``docs/audit/PHYSICAL_REALISM_REPORT.md``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from synthetic_generator.domains.bms_classrooms.physics.indoor import (
    simulate_noise,
)


def _step_occupancy(n: int = 240, freq_seconds: int = 5) -> tuple[pd.DatetimeIndex, pd.Series]:
    """Genera 20 min @ 5 s con un step de ocupación 0 → 20 a la mitad."""
    index = pd.date_range("2026-05-09T08:00:00Z", periods=n, freq=f"{freq_seconds}s")
    values = np.zeros(n, dtype=int)
    values[n // 2 :] = 20
    return index, pd.Series(values, index=index, name="occupancy")


@pytest.mark.integration
def test_legacy_no_tau_keeps_step() -> None:
    """Sin tau_minutes el comportamiento legacy se preserva (step grande)."""
    index, occ = _step_occupancy()
    rng = np.random.default_rng(42)
    cfg = {"base_unoccupied": 33.0, "base_occupied": 55.0, "std": 0.0}
    out = simulate_noise(index, occ, cfg, rng)
    # En la transición 0→20 hay un salto > 15 dB en 1 sample (sin EWMA).
    transition_idx = len(out) // 2
    delta = abs(float(out.iloc[transition_idx] - out.iloc[transition_idx - 1]))
    assert delta > 15.0, f"Sin EWMA esperamos salto > 15 dB en transición, got {delta:.2f}"


@pytest.mark.integration
def test_tau_zero_is_escape_hatch() -> None:
    """``tau_minutes=0`` desactiva EWMA (= legacy)."""
    index, occ = _step_occupancy()
    cfg_legacy = {"base_unoccupied": 33.0, "base_occupied": 55.0, "std": 0.0}
    cfg_zero = {**cfg_legacy, "tau_minutes": 0.0}

    rng_a = np.random.default_rng(42)
    out_legacy = simulate_noise(index, occ, cfg_legacy, rng_a)
    rng_b = np.random.default_rng(42)
    out_zero = simulate_noise(index, occ, cfg_zero, rng_b)
    np.testing.assert_array_almost_equal(out_legacy.values, out_zero.values)


@pytest.mark.integration
def test_tau_3min_smooths_transition() -> None:
    """Con tau=3 min, salto consecutivo p99 ≤ ~3 dB en transición (sin ruido)."""
    index, occ = _step_occupancy(n=480)
    rng = np.random.default_rng(42)
    cfg = {
        "base_unoccupied": 33.0,
        "base_occupied": 55.0,
        "std": 0.0,
        "tau_minutes": 3.0,
    }
    out = simulate_noise(index, occ, cfg, rng)
    diffs = out.diff().abs().dropna()
    # Con tau=3 min, alpha = 5/180 = 0.0278; salto inicial ~0.0278 * 22 = 0.6 dB.
    # Tolerancia ≤ 3 dB para cubrir margen.
    p99 = float(np.quantile(diffs.values, 0.99))
    assert p99 <= 3.0, f"Con tau=3 min, p99 |Δn| consecutivo debería ser ≤ 3 dB, got {p99:.2f}"


@pytest.mark.integration
def test_ewma_converges_to_target() -> None:
    """Tras ~5·tau el output converge al target."""
    index, occ = _step_occupancy(n=720)  # 60 min
    rng = np.random.default_rng(42)
    cfg = {
        "base_unoccupied": 33.0,
        "base_occupied": 55.0,
        "std": 0.0,
        "tau_minutes": 3.0,
    }
    out = simulate_noise(index, occ, cfg, rng)
    # Target en occ=20: 55 + 0.35 * 20 = 62 dB.
    final = float(out.iloc[-1])
    assert abs(final - 62.0) < 1.0, f"Sin convergencia: final {final:.2f} dB, esperado ~62 ± 1"


@pytest.mark.integration
def test_initial_value_matches_target() -> None:
    """``smoothed[0]`` arranca en el target, no en un valor arbitrario."""
    index, occ = _step_occupancy()
    rng = np.random.default_rng(42)
    cfg = {
        "base_unoccupied": 33.0,
        "base_occupied": 55.0,
        "std": 0.0,
        "tau_minutes": 3.0,
    }
    out = simulate_noise(index, occ, cfg, rng)
    # Sample 0: occ=0 → target=33. Output debe ser exactamente 33 (std=0).
    assert abs(float(out.iloc[0]) - 33.0) < 0.01, (
        f"smoothed[0] debería arrancar en target=33, got {out.iloc[0]:.2f}"
    )
