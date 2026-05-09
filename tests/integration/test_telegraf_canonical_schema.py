"""Auditoría estática del schema canonical CAPTIA en Telegraf.

Validado con queries reales contra InfluxDB durante audit live (10-may-2026):
producción simarro-prod (PPTX slide 5) eliminó los tags ``host`` y ``topic``
del measurement ``captia_point`` con commit c1997bb (cardinality reduction).

Este test verifica que la config Telegraf NO emite esos tags:
  - ``omit_hostname = true`` en agent (drops host).
  - ``processors.tag_limit`` con keep = 5 tags canónicos (drops topic + extras).

Cierra bug detectado en audit live de 10-may-2026.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAF_CONF = REPO_ROOT / "infra" / "telegraf" / "telegraf.conf"

CANONICAL_TAGS = {"captia_env", "domain_id", "site_id", "asset_id", "variable"}


def _load_telegraf() -> dict:
    with TELEGRAF_CONF.open("rb") as f:
        return tomllib.load(f)


@pytest.mark.integration
def test_telegraf_omits_hostname_tag() -> None:
    """Schema canonical PPTX slide 5: tag ``host`` eliminado por commit c1997bb."""
    data = _load_telegraf()
    omit = data["agent"].get("omit_hostname", False)
    assert omit is True, (
        "agent.omit_hostname debe ser true para evitar tag 'host' en captia_point. "
        "Producción simarro-prod lo eliminó (cardinality reduction commit c1997bb 2026-04-13)."
    )


@pytest.mark.integration
def test_telegraf_has_tag_limit_processor() -> None:
    """Debe existir processor tag_limit que restrinja tags a los 5 canónicos.

    Sin esto, el tag `topic` (usado para extracción regex) queda emitido a
    InfluxDB e infla cardinality 13× según producción (PPTX slide 5).
    """
    data = _load_telegraf()
    tag_limits = data.get("processors", {}).get("tag_limit", [])
    assert tag_limits, (
        "Falta [[processors.tag_limit]] — sin esto el tag 'topic' aterriza en "
        "captia_point inflando cardinality."
    )

    # Encontrar el tag_limit que afecta captia_point.
    target = None
    for tl in tag_limits:
        namepass = tl.get("namepass", [])
        if "captia_point" in namepass or "captia_cmd_event" in namepass:
            target = tl
            break
    assert target is not None, "No tag_limit aplica a namepass=['captia_point', ...]"

    keep = set(target.get("keep", []))
    assert keep == CANONICAL_TAGS, (
        f"tag_limit.keep debe ser exactamente los 5 tags canónicos.\n"
        f"  esperado: {sorted(CANONICAL_TAGS)}\n"
        f"  got:      {sorted(keep)}"
    )

    limit = target.get("limit", 0)
    assert limit == 5, f"tag_limit.limit debe ser 5 (canonical), got {limit}"


@pytest.mark.integration
def test_telegraf_tag_limit_runs_after_regex() -> None:
    """tag_limit debe estar definido DESPUÉS de processors.regex en el TOML.

    Telegraf ejecuta processors en orden de definición. Si tag_limit corre antes
    de regex, los 5 tags no se han extraído todavía y se pierden.
    """
    text = TELEGRAF_CONF.read_text(encoding="utf-8")
    regex_pos = text.find("[[processors.regex]]")
    tag_limit_pos = text.find("[[processors.tag_limit]]")
    assert regex_pos > 0, "[[processors.regex]] no encontrado"
    assert tag_limit_pos > 0, "[[processors.tag_limit]] no encontrado"
    assert tag_limit_pos > regex_pos, (
        "[[processors.tag_limit]] debe definirse DESPUÉS de [[processors.regex]] "
        "para que los 5 tags estén extraídos cuando se aplica el filtro."
    )


@pytest.mark.integration
def test_telegraf_tag_limit_runs_before_clone() -> None:
    """tag_limit debe ejecutarse ANTES de clone para que el clon no herede tags extras."""
    text = TELEGRAF_CONF.read_text(encoding="utf-8")
    tag_limit_pos = text.find("[[processors.tag_limit]]")
    clone_pos = text.find("[[processors.clone]]")
    assert clone_pos > 0
    assert tag_limit_pos > 0
    assert tag_limit_pos < clone_pos, (
        "[[processors.tag_limit]] debe ir ANTES de [[processors.clone]] "
        "para que el state_events clone NO incluya host/topic."
    )
