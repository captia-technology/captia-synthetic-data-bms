"""Auditoría de jitter del setpoint (H-23, PATCH 002).

Verifica que ``vendor/.../physics/actuators.py:thermostat_setpoint`` ahora
expone ``setpoint_jitter_std`` y ``setpoint_manual_jitter_std`` como claves
de configuración con backward-compat de 0.3 / 0.8 cuando faltan.

Cierra el hallazgo H-23 documentado en ``docs/audit/PHYSICAL_REALISM_REPORT.md``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from synthetic_generator.domains.bms_classrooms.physics.actuators import (
    thermostat_setpoint,
)


@pytest.fixture
def stable_scene() -> pd.Series:
    """120 samples (~10 min @ 5 s) en escena estable ``class``."""
    index = pd.date_range("2026-05-09T08:00:00Z", periods=120, freq="5s")
    return pd.Series(["class"] * len(index), index=index, name="scene_mode")


def _p99_consecutive_delta(series: pd.Series) -> float:
    diffs = series.diff().dropna().abs()
    return float(np.quantile(diffs.values, 0.99))


@pytest.mark.integration
def test_default_jitter_preserves_legacy_behaviour(stable_scene: pd.Series) -> None:
    """Sin override en cfg, el jitter sigue siendo el legacy 0.3 (R-RETRO)."""
    rng = np.random.default_rng(42)
    sp = thermostat_setpoint(
        scene=stable_scene,
        cfg_indoor={"setpoint_class": 21.0, "setpoint_out_of_hours": 18.0},
        rng=rng,
    )
    # std esperada ~ 0.3 (jitter por sample) — toleramos ±20 % por tamaño finito.
    assert 0.20 < float(sp.std()) < 0.40, (
        f"Default legacy jitter perdido: std observada {sp.std():.4f}"
    )


@pytest.mark.integration
def test_jitter_zero_yields_exact_setpoint(stable_scene: pd.Series) -> None:
    """Con ``setpoint_jitter_std=0`` y escena estable, el setpoint es exacto."""
    rng = np.random.default_rng(42)
    sp = thermostat_setpoint(
        scene=stable_scene,
        cfg_indoor={
            "setpoint_class": 21.0,
            "setpoint_out_of_hours": 18.0,
            "setpoint_jitter_std": 0.0,
            "setpoint_manual_jitter_std": 0.0,
        },
        rng=rng,
    )
    assert (sp == 21.0).all(), "Con jitter_std=0 todos los setpoints deberían ser 21.0"


@pytest.mark.integration
def test_jitter_005_keeps_consecutive_delta_low(stable_scene: pd.Series) -> None:
    """Con ``setpoint_jitter_std=0.05`` (override del repo), |Δsp| consecutivo p99 ≤ 0.2 °C.

    Esta es la corrección H-23: el override actual de ``domain.yaml`` debe
    producir setpoints físicamente estables (cambia con escena, no con jitter
    sample-a-sample).
    """
    rng = np.random.default_rng(42)
    sp = thermostat_setpoint(
        scene=stable_scene,
        cfg_indoor={
            "setpoint_class": 21.0,
            "setpoint_out_of_hours": 18.0,
            "setpoint_jitter_std": 0.05,
        },
        rng=rng,
    )
    p99_delta = _p99_consecutive_delta(sp)
    assert p99_delta <= 0.2, (
        f"Con setpoint_jitter_std=0.05 el p99 de |Δsp| consecutivo debería ser ≤ 0.2 °C "
        f"(observado {p99_delta:.4f})"
    )


@pytest.mark.integration
def test_jitter_005_reduces_event_count_vs_default(stable_scene: pd.Series) -> None:
    """Con jitter 0.05 vs default 0.3, los eventos on-change caen al menos 5× sobre la prueba.

    Aproximamos un detector on-change con umbral 0.1 °C (típico Telegraf
    processors.dedup) y contamos transiciones que cruzan ese umbral.
    """
    rng_default = np.random.default_rng(42)
    rng_low = np.random.default_rng(42)

    sp_default = thermostat_setpoint(
        scene=stable_scene,
        cfg_indoor={"setpoint_class": 21.0, "setpoint_out_of_hours": 18.0},
        rng=rng_default,
    )
    sp_low = thermostat_setpoint(
        scene=stable_scene,
        cfg_indoor={
            "setpoint_class": 21.0,
            "setpoint_out_of_hours": 18.0,
            "setpoint_jitter_std": 0.05,
        },
        rng=rng_low,
    )

    threshold = 0.1
    on_change_default = int((sp_default.diff().abs() > threshold).sum())
    on_change_low = int((sp_low.diff().abs() > threshold).sum())

    assert on_change_low * 5 <= on_change_default, (
        f"H-23 no se materializa: default={on_change_default} on-change "
        f"vs low={on_change_low} (esperado ratio ≥ 5×)"
    )
