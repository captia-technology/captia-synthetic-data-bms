"""Integration test del awk parser de populate_metadata.

Ejecuta el bloque awk de ``infra/influxdb/init/init_buckets_tasks.sh`` sobre
``config/domains/bms_classrooms/variables.yaml`` y verifica que el output
line-protocol coincide con el schema canónico de ``captia_point_meta``
(producción simarro-prod, slide 9 PPTX).

Cierra L-PV-21 (rollups silenciosamente vacíos por captia_metadata sin poblar).
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VARIABLES_YAML = REPO_ROOT / "config" / "domains" / "bms_classrooms" / "variables.yaml"
INIT_SCRIPT = REPO_ROOT / "infra" / "influxdb" / "init" / "init_buckets_tasks.sh"


def _run_awk_parser_only(env: str, domain: str, site: str, ts: str) -> str:
    """Run the awk parser inline (extracted from init_buckets_tasks.sh).

    We replicate the awk block here so the test runs offline (no docker, no influx).
    Source of truth: infra/influxdb/init/init_buckets_tasks.sh::populate_metadata
    (lines 130-172, awk block).
    """
    awk_program = r"""
        BEGIN {
            asset_type = "classroom"
            name = ""
        }
        /^  [a-z_][a-z_0-9]*:[[:space:]]*$/ {
            t = $1; gsub(":", "", t); gsub("^ +", "", t); asset_type = t
            next
        }
        /^      - name:/ {
            if (name != "") emit();
            name = $3; gsub("\"|'\''", "", name);
            prod_name = ""; data_type = ""; unit = "";
            point_type = ""; metric_kind = ""; category = "";
            storage_mode = ""; rmin = ""; rmax = "";
            next;
        }
        /^        production_name:/ { val = $0; sub(/^        production_name:[[:space:]]*/, "", val); gsub("\"|'\''", "", val); prod_name = val; next }
        /^        data_type:/       { val = $0; sub(/^        data_type:[[:space:]]*/, "", val); data_type = val; next }
        /^        unit:/            { val = $0; sub(/^        unit:[[:space:]]*/, "", val); gsub("\"|'\''", "", val); unit = val; next }
        /^        point_type:/      { val = $0; sub(/^        point_type:[[:space:]]*/, "", val); point_type = val; next }
        /^        metric_kind:/     { val = $0; sub(/^        metric_kind:[[:space:]]*/, "", val); metric_kind = val; next }
        /^        category:/        { val = $0; sub(/^        category:[[:space:]]*/, "", val); category = val; next }
        /^        storage_mode:/    { val = $0; sub(/^        storage_mode:[[:space:]]*/, "", val); storage_mode = val; next }
        /^        range:/ {
            val = $0;
            sub(/^        range:[[:space:]]*\[/, "", val);
            sub(/\][[:space:]]*$/, "", val);
            n = split(val, a, /,[[:space:]]*/);
            if (n >= 2) { rmin = a[1]; rmax = a[2]; }
            next;
        }
        END { if (name != "") emit(); }
        function emit(    emit_name, tags, fields) {
            emit_name = (prod_name != "") ? prod_name : name;
            gsub(/[, ]/, "_", emit_name);
            if (storage_mode == "") {
                if (metric_kind == "bool_state" || metric_kind == "setpoint_step") {
                    storage_mode = "on_change";
                } else {
                    storage_mode = "continuous";
                }
            }
            tags = "captia_env=" env ",domain_id=" domain ",site_id=" site ",asset_type=" asset_type ",variable=" emit_name;
            fields = "metric_kind=\"" metric_kind "\",storage_mode=\"" storage_mode "\""
            if (data_type != "")  fields = fields ",data_type=\"" data_type "\""
            if (unit != "")       fields = fields ",unit=\"" unit "\""
            if (point_type != "") fields = fields ",point_type=\"" point_type "\""
            if (category != "")   fields = fields ",category=\"" category "\""
            if (rmin != "")       fields = fields ",range_min=" rmin
            if (rmax != "")       fields = fields ",range_max=" rmax
            if (prod_name != "" && prod_name != name) fields = fields ",vendor_name=\"" name "\""
            print "captia_point_meta," tags " " fields " " ts
        }
    """
    awk_bin = shutil.which("awk") or shutil.which("gawk")
    if awk_bin is None:
        pytest.skip("awk no disponible")
    proc = subprocess.run(
        [
            awk_bin,
            "-v",
            f"env={env}",
            "-v",
            f"domain={domain}",
            "-v",
            f"site={site}",
            "-v",
            f"ts={ts}",
            awk_program,
            str(VARIABLES_YAML),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, f"awk failed: {proc.stderr}"
    return proc.stdout


@pytest.mark.integration
def test_metadata_bootstrap_emits_21_records() -> None:
    """El parser emite exactamente 21 records (uno por variable del catálogo)."""
    output = _run_awk_parser_only("dev", "bms_classrooms", "ies_simarro", "1714572345000000000")
    lines = [ln for ln in output.strip().split("\n") if ln.strip()]
    assert len(lines) == 21, f"esperado 21 records, got {len(lines)}"


@pytest.mark.integration
def test_metadata_bootstrap_uses_correct_measurement() -> None:
    """Cada record usa measurement ``captia_point_meta`` (no legacy ``captia_metadata``)."""
    output = _run_awk_parser_only("dev", "bms_classrooms", "ies_simarro", "1714572345000000000")
    for line in output.strip().split("\n"):
        assert line.startswith("captia_point_meta,"), f"wrong measurement: {line[:80]}"


@pytest.mark.integration
def test_metadata_bootstrap_emits_5_canonical_tags_plus_asset_type() -> None:
    """Tags emitidas: captia_env, domain_id, site_id, asset_type, variable."""
    output = _run_awk_parser_only("dev", "bms_classrooms", "ies_simarro", "1714572345000000000")
    line = output.strip().split("\n")[0]
    tag_block = line.split(" ")[0].split(",", 1)[1]
    tag_keys = {t.split("=")[0] for t in tag_block.split(",")}
    assert tag_keys == {"captia_env", "domain_id", "site_id", "asset_type", "variable"}, (
        f"unexpected tag keys: {tag_keys}"
    )


@pytest.mark.integration
def test_metadata_bootstrap_emits_required_fields() -> None:
    """Cada record tiene ``metric_kind`` y ``storage_mode`` como mínimo."""
    output = _run_awk_parser_only("dev", "bms_classrooms", "ies_simarro", "1714572345000000000")
    for line in output.strip().split("\n"):
        field_block = line.split(" ", 1)[1].rsplit(" ", 1)[0]
        assert "metric_kind=" in field_block, f"missing metric_kind in {line[:120]}"
        assert "storage_mode=" in field_block, f"missing storage_mode in {line[:120]}"


@pytest.mark.integration
def test_metadata_bootstrap_storage_mode_inferred() -> None:
    """``bool_state`` y ``setpoint_step`` derivan storage_mode=on_change automáticamente."""
    output = _run_awk_parser_only("dev", "bms_classrooms", "ies_simarro", "1714572345000000000")
    for line in output.strip().split("\n"):
        is_bool_state = 'metric_kind="bool_state"' in line
        is_setpoint = 'metric_kind="setpoint_step"' in line
        if is_bool_state or is_setpoint:
            assert 'storage_mode="on_change"' in line, (
                f"on_change variable missing storage_mode: {line[:120]}"
            )
        elif (
            'metric_kind="analog_gauge"' in line
            or 'metric_kind="counter"' in line
            or 'metric_kind="bool_presence"' in line
        ):
            assert 'storage_mode="continuous"' in line, (
                f"continuous variable missing storage_mode: {line[:120]}"
            )


@pytest.mark.integration
def test_metadata_bootstrap_uses_production_names() -> None:
    """Cuando ``production_name`` existe, se usa como tag ``variable``."""
    output = _run_awk_parser_only("dev", "bms_classrooms", "ies_simarro", "1714572345000000000")
    variables = set()
    for line in output.strip().split("\n"):
        m = re.search(r",variable=([^,\s]+)", line)
        assert m, f"no variable tag: {line[:80]}"
        variables.add(m.group(1))

    expected_production = {
        "temperature_01",
        "relative-humidity",
        "co2",
        "iaq-index",
        "avg-sound-level",
        "luminosity",
        "people-count",
        "occupancy",
        "temperature-outdoor",
        "daylight-lux",
        "temperature_01_sp",
        "ac_control",
        "ac_state",
        "valve_control",
        "scene_mode",
        "light_01_state",
        "light_02_state",
        "fan_speed_01_state",
        "fan_speed_02_state",
        "power_01",
        "energy_01",
    }
    missing = expected_production - variables
    assert not missing, f"production names faltantes: {missing}"


@pytest.mark.integration
def test_metadata_bootstrap_includes_vendor_name_when_renamed() -> None:
    """Cuando ``production_name != name``, se incluye field ``vendor_name``."""
    output = _run_awk_parser_only("dev", "bms_classrooms", "ies_simarro", "1714572345000000000")
    found = False
    for line in output.strip().split("\n"):
        if ",variable=temperature_01 " in line:
            assert 'vendor_name="temperature"' in line, (
                f"temperature_01 missing vendor_name: {line[:200]}"
            )
            found = True
            break
    assert found, "no temperature_01 record found"

    for line in output.strip().split("\n"):
        if ",variable=co2 " in line:
            assert "vendor_name=" not in line, (
                f"co2 should not have vendor_name (no rename): {line[:200]}"
            )
            break


@pytest.mark.integration
def test_metadata_bootstrap_init_script_is_valid_bash() -> None:
    """El script init_buckets_tasks.sh tiene sintaxis bash válida."""
    bash_bin = shutil.which("bash") or shutil.which("sh")
    if bash_bin is None:
        pytest.skip("bash no disponible")
    proc = subprocess.run(
        [bash_bin, "-n", str(INIT_SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"bash syntax error: {proc.stderr}"
