"""Auditoría de TZ-awareness en ScenarioRunner._publisher_loop (H-21 / PATCH 005).

Verifica que ``datetime.now(tz=ZoneInfo(sim.timezone))`` produce un
``datetime`` TZ-aware en la zona horaria del escenario, eliminando el
drift de 1-2 h (DST) entre wall-clock y reloj simulado.

Cierra el hallazgo H-21 documentado en
``docs/audit/E2E_VALIDATION_REPORT.md``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest


@pytest.mark.integration
def test_tz_aware_datetime_madrid() -> None:
    """``ZoneInfo("Europe/Madrid")`` produce datetime con offset +01:00 o +02:00."""
    tz = ZoneInfo("Europe/Madrid")
    now = datetime.now(tz=tz)
    assert now.tzinfo is not None, "datetime debe ser TZ-aware"
    offset = now.utcoffset()
    assert offset is not None
    seconds = int(offset.total_seconds())
    # Madrid: UTC+1 (CET, invierno) o UTC+2 (CEST, verano)
    assert seconds in {3600, 7200}, (
        f"Offset Madrid debería ser +01:00 (3600 s) o +02:00 (7200 s), got {seconds}"
    )


@pytest.mark.integration
def test_tz_aware_datetime_utc() -> None:
    """``timezone.utc`` produce datetime con offset 0."""
    now = datetime.now(tz=timezone.utc)
    assert now.tzinfo is not None
    assert now.utcoffset() is not None
    assert int(now.utcoffset().total_seconds()) == 0


@pytest.mark.integration
def test_naive_datetime_is_what_was_broken() -> None:
    """Caracteriza el bug previo: ``datetime.now()`` sin tz devuelve naive datetime."""
    now = datetime.now()  # explicit el comportamiento previo
    assert now.tzinfo is None, "datetime.now() sin tz es naive (esto era el bug H-21)"


@pytest.mark.integration
def test_runner_imports_zoneinfo() -> None:
    """``vendor/.../core/runner.py`` importa ZoneInfo (parche aplicado)."""
    from pathlib import Path

    runner_py = (
        Path(__file__).resolve().parents[2]
        / "vendor"
        / "synthetic-generator"
        / "src"
        / "synthetic_generator"
        / "core"
        / "runner.py"
    )
    text = runner_py.read_text(encoding="utf-8")
    assert "from zoneinfo import ZoneInfo" in text, (
        "PATCH 005 no aplicado: runner.py no importa ZoneInfo"
    )
    assert "datetime.now(tz=sim_tz)" in text, (
        "PATCH 005 no aplicado: runner.py sigue usando datetime.now() naive"
    )
