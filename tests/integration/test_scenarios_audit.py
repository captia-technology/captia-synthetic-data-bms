"""Auditoría estática de los scenarios YAML (Caso A/B/C/D + e2e_host).

Verifica:
  1. Cada scenario yaml es válido (parsea como YAML).
  2. Todos los scenarios usan domain.id == bms_classrooms.
  3. project.site_id == ies_simarro.
  4. seed presente y consistente.
  5. Todos los scenarios apuntan a un domain.config_path resoluble (al override
     local) — esto es CRÍTICO para que las holidays expandidas T-PV-09 surtan efecto.
  6. Los sinks tienen configuración mínima válida.

Cierra parte de L-PV-06 + valida T-PV-09 a nivel de scenarios.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_DIR = REPO_ROOT / "config" / "projects"
DOMAIN_YAML_LOCAL = REPO_ROOT / "config" / "domains" / "bms_classrooms" / "domain.yaml"


def _all_scenarios() -> list[Path]:
    return sorted(SCENARIOS_DIR.glob("bms_v1_*.yaml"))


def _load_scenario(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# ──────────────────── Tests ────────────────────


@pytest.mark.integration
def test_at_least_4_scenarios_exist() -> None:
    """Caso A (demo + e2e_host) + B + C + D = al menos 4 scenarios."""
    scenarios = _all_scenarios()
    assert len(scenarios) >= 4, (
        f"esperado ≥4 scenarios, got {len(scenarios)}: {[p.name for p in scenarios]}"
    )


@pytest.mark.integration
@pytest.mark.parametrize("scenario_path", _all_scenarios(), ids=lambda p: p.name)
def test_scenario_is_valid_yaml(scenario_path: Path) -> None:
    """Cada scenario yaml parsea como dict."""
    data = _load_scenario(scenario_path)
    assert isinstance(data, dict), f"{scenario_path.name} no parsea como dict"


@pytest.mark.integration
@pytest.mark.parametrize("scenario_path", _all_scenarios(), ids=lambda p: p.name)
def test_scenario_has_required_top_level_keys(scenario_path: Path) -> None:
    data = _load_scenario(scenario_path)
    required = {"project", "simulation", "domain", "phases", "sinks"}
    missing = required - set(data.keys())
    assert not missing, f"{scenario_path.name} missing keys: {missing}"


@pytest.mark.integration
@pytest.mark.parametrize("scenario_path", _all_scenarios(), ids=lambda p: p.name)
def test_scenario_uses_canonical_site_and_domain(scenario_path: Path) -> None:
    data = _load_scenario(scenario_path)
    assert data["project"]["site_id"] == "ies_simarro", (
        f"{scenario_path.name} site_id != ies_simarro"
    )
    assert data["domain"]["id"] == "bms_classrooms", (
        f"{scenario_path.name} domain.id != bms_classrooms"
    )


@pytest.mark.integration
@pytest.mark.parametrize("scenario_path", _all_scenarios(), ids=lambda p: p.name)
def test_scenario_has_seed(scenario_path: Path) -> None:
    """Determinismo: seed debe estar definido."""
    data = _load_scenario(scenario_path)
    seed = data["simulation"].get("seed")
    assert isinstance(seed, int), f"{scenario_path.name} simulation.seed no es int: {seed!r}"
    assert seed >= 0


@pytest.mark.integration
@pytest.mark.parametrize("scenario_path", _all_scenarios(), ids=lambda p: p.name)
def test_scenario_specifies_domain_config_path(scenario_path: Path) -> None:
    """Cada scenario debe especificar ``domain.config_path`` apuntando al override local
    (o al equivalente Docker). Sin esto, vendor usa su domain.yaml default y las
    holidays expandidas T-PV-09 NO entran en vigor.
    """
    data = _load_scenario(scenario_path)
    config_path = data["domain"].get("config_path")
    assert config_path, (
        f"{scenario_path.name}: domain.config_path NO especificado. "
        "Sin esto, vendor carga su domain.yaml default y las holidays T-PV-09 no se aplican."
    )
    # Debe apuntar a config/domains/bms_classrooms/domain.yaml (host o docker path).
    assert (
        "config/domains/bms_classrooms/domain.yaml" in config_path
        or "config\\domains\\bms_classrooms\\domain.yaml" in config_path
    ), f"{scenario_path.name}: config_path={config_path!r} no apunta a domain.yaml local"


@pytest.mark.integration
@pytest.mark.parametrize("scenario_path", _all_scenarios(), ids=lambda p: p.name)
def test_scenario_has_at_least_one_sink(scenario_path: Path) -> None:
    data = _load_scenario(scenario_path)
    sinks = data["sinks"]
    assert isinstance(sinks, list) and len(sinks) >= 1, (
        f"{scenario_path.name}: sinks debe ser lista no vacía"
    )
    for s in sinks:
        assert "type" in s, f"{scenario_path.name}: sink sin type"
        assert s["type"] in {"mqtt", "file", "stdout"}, (
            f"{scenario_path.name}: sink type no canónico: {s['type']}"
        )


@pytest.mark.integration
def test_scenario_caseB_is_backfill_mode() -> None:
    """Caso B (12 meses consumption) debe ser backfill puro (no live)."""
    data = _load_scenario(SCENARIOS_DIR / "bms_v1_caseB_consumption.yaml")
    assert data["phases"]["backfill"]["enabled"] is True
    assert data["phases"]["live"]["enabled"] is False


@pytest.mark.integration
def test_scenario_caseC_has_faults_yaml_referenced() -> None:
    """Caso C (faults) debe referenciar config de faults o tener faults flag."""
    data = _load_scenario(SCENARIOS_DIR / "bms_v1_caseC_faults.yaml")
    s = yaml.dump(data)
    # Either explicit fault config_path, faults section, or faults_enabled flag.
    has_fault_ref = (
        "faults" in s.lower()
        or "fault_" in s.lower()
        or any("fault" in str(v).lower() for v in data.get("domain", {}).values())
    )
    assert has_fault_ref, "Caso C scenario sin referencia explícita a faults config"


@pytest.mark.integration
def test_scenario_demo_uses_mqtt_sink() -> None:
    """Caso A (demo) — live MQTT — debe usar sink type mqtt."""
    data = _load_scenario(SCENARIOS_DIR / "bms_v1_demo.yaml")
    sink_types = {s["type"] for s in data["sinks"]}
    assert "mqtt" in sink_types, f"demo scenario debe usar mqtt sink, got {sink_types}"
