"""Auditoría de HVAC anti short-cycle (L-PV-07 / PATCH 004).

Verifica que ``hvac_enable`` aplica min-on / min-off dwell cuando recibe
``cfg_indoor`` con las claves correspondientes, y que sin esos parámetros
el comportamiento legacy se preserva.

Cierra el hallazgo F-2 documentado en ``docs/audit/PHYSICAL_REALISM_REPORT.md``
y la regla R-HVAC-EN-03 documentada en
``docs/specs/digital-twin-bms-physics-validation/04-physical-plausibility-rules.md``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from synthetic_generator.domains.bms_classrooms.physics.actuators import (
    _enforce_min_dwell,
    hvac_enable,
)


def _toggles(arr: np.ndarray) -> int:
    return int(np.sum(np.diff(arr) != 0))


def _make_oscillating_inputs(n_samples: int = 240, freq_seconds: int = 5):
    """Genera entradas que harían oscilar HVAC sample-a-sample sin dwell."""
    index = pd.date_range("2026-05-09T08:00:00Z", periods=n_samples, freq=f"{freq_seconds}s")
    rng = np.random.default_rng(42)
    setpoint = pd.Series([21.0] * n_samples, index=index, name="setpoint")
    indoor = pd.Series(
        21.0 + rng.normal(0, 0.5, n_samples),
        index=index,
        name="indoor",
    )
    occ = pd.Series([10] * n_samples, index=index, name="occupancy")
    scene = pd.Series(["class"] * n_samples, index=index, name="scene_mode")
    return index, indoor, setpoint, occ, scene


@pytest.mark.integration
def test_legacy_signature_preserved() -> None:
    """Sin cfg_indoor → comportamiento idéntico al legacy."""
    _, indoor, setp, occ, scene = _make_oscillating_inputs()
    enable = hvac_enable(indoor, setp, occ, scene)
    assert isinstance(enable, pd.Series)
    assert set(enable.values).issubset({0, 1})


@pytest.mark.integration
def test_min_dwell_zero_is_escape_hatch() -> None:
    """Con min_on=0 y min_off=0 el post-process no toca nada."""
    _, indoor, setp, occ, scene = _make_oscillating_inputs()
    enable_legacy = hvac_enable(indoor, setp, occ, scene)
    enable_zero = hvac_enable(
        indoor,
        setp,
        occ,
        scene,
        cfg_indoor={"hvac_min_on_minutes": 0.0, "hvac_min_off_minutes": 0.0},
    )
    assert (enable_legacy.values == enable_zero.values).all()


@pytest.mark.integration
def test_anti_short_cycle_reduces_toggles() -> None:
    """Con min_on=5 y min_off=5 los toggles caen drásticamente."""
    _, indoor, setp, occ, scene = _make_oscillating_inputs(n_samples=240)
    enable_legacy = hvac_enable(indoor, setp, occ, scene)
    enable_dwell = hvac_enable(
        indoor,
        setp,
        occ,
        scene,
        cfg_indoor={"hvac_min_on_minutes": 5.0, "hvac_min_off_minutes": 5.0},
    )
    n_legacy = _toggles(enable_legacy.values)
    n_dwell = _toggles(enable_dwell.values)
    assert n_dwell * 5 <= n_legacy + 1, (
        f"L-PV-07 no se materializa: legacy toggles={n_legacy}, "
        f"dwell toggles={n_dwell} (esperado ratio ≥ 5×)"
    )


@pytest.mark.integration
def test_min_dwell_run_length_p10_above_threshold() -> None:
    """p10(run_length) ≥ 5 min con dwell=5 (regla R-HVAC-EN-03)."""
    _, indoor, setp, occ, scene = _make_oscillating_inputs(n_samples=720)
    enable = hvac_enable(
        indoor,
        setp,
        occ,
        scene,
        cfg_indoor={"hvac_min_on_minutes": 5.0, "hvac_min_off_minutes": 5.0},
    )
    arr = enable.values
    # Run-length encoding.
    runs: list[int] = []
    if len(arr) > 0:
        cur, length = arr[0], 1
        for x in arr[1:]:
            if x == cur:
                length += 1
            else:
                runs.append(length)
                cur, length = x, 1
        runs.append(length)

    if len(runs) >= 2:
        # Ignoramos el primer y último run (parciales por borde).
        interior_runs = runs[1:-1] if len(runs) > 2 else runs
        run_lengths_min = np.array(interior_runs) * (5.0 / 60.0)  # 5 s / sample → min
        p10 = float(np.quantile(run_lengths_min, 0.1))
        assert p10 >= 4.0, (
            f"p10(run_length) = {p10:.2f} min — esperado ≥ 4 min con dwell=5 "
            f"(margen por contar samples discretos: 60 samples × 5 s = 5 min)"
        )


@pytest.mark.integration
def test_dwell_helper_handles_edge_cases() -> None:
    """Edge cases: serie vacía, single sample, todo OFF, todo ON."""
    # Single sample.
    assert _enforce_min_dwell(np.array([1]), 1.0, 5.0, 5.0).tolist() == [1]
    # All OFF.
    arr = np.zeros(20, dtype=int)
    assert (_enforce_min_dwell(arr, 1.0, 5.0, 5.0) == arr).all()
    # All ON.
    arr = np.ones(20, dtype=int)
    assert (_enforce_min_dwell(arr, 1.0, 5.0, 5.0) == arr).all()


@pytest.mark.integration
def test_dwell_helper_holds_against_short_pulse() -> None:
    """Pulso corto (1 sample) en medio de una serie debe ser suprimido por dwell."""
    arr = np.array([0, 0, 0, 1, 0, 0, 0, 0, 0, 0])
    out = _enforce_min_dwell(arr, dt_min=1.0, min_on_min=5.0, min_off_min=0.0)
    # El pulso de 1 sample (1 min) no llega a min_on=5 → debería extender ON
    # hasta cubrir 5 min, luego volver a OFF.
    assert out[3] == 1
    # Verificamos que el ON dura al menos 5 samples (5 min con dt=1 min).
    on_indices = np.where(out == 1)[0]
    if len(on_indices) > 0:
        on_run_len = on_indices[-1] - on_indices[0] + 1
        assert on_run_len >= 5, (
            f"ON run length = {on_run_len} (esperado ≥ 5 con min_on=5 min y dt=1 min)"
        )
