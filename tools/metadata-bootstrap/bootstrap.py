#!/usr/bin/env python3
"""Metadata Bootstrap — populate captia_metadata bucket from variables.yaml.

Adapted from captia-connect/tools/metadata-bootstrap/bootstrap.py with these
local additions:
  - Honors `production_name:` override per variable (renames vendor → prod
    name to match simarro-prod ground-truth — see L-PV-01).
  - Single domain by default (`bms_classrooms`); multi-domain optional.
  - Auto-expands assets: AULA01..AULAnn based on BMS_N_AULAS env or
    `--n-aulas` flag.
  - Designed for AUTOMATIC execution on every deploy (no profile gate).

Writes 2 measurements to bucket `captia_metadata`:
  captia_point_meta   — one row per (asset_id, variable) with full schema.
  captia_domain_meta  — one row per domain with namespace, templates, etc.

Tags aligned with telemetry (so dashboards can JOIN):
  shared:   domain_id, site_id, variable, captia_env
  meta-only: asset_id (instance), asset_type (class)

Usage:
  python bootstrap.py --url http://influxdb:8086 --token XXX --org captia
  python bootstrap.py --dry-run                    # print line-protocol only
  python bootstrap.py --skip-if-exists             # idempotent (default in deploy)
  python bootstrap.py --force                      # purge + rewrite
  python bootstrap.py --diagnose                   # connectivity + 1-line write test

Exit codes:
  0   ok (or skip-if-exists hit)
  1   error (config missing, influx down, write failed)
  130 SIGINT
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import yaml
from influxdb_client import InfluxDBClient, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

METADATA_BUCKET = "captia_metadata"
VARIABLE_MEASUREMENT = "captia_point_meta"
DOMAIN_MEASUREMENT = "captia_domain_meta"

# metric_kind → storage_mode mapping (mirrors adapter spec).
_METRIC_KIND_STORAGE_MAP = {
    "setpoint_step": "on_change",
    "bool_state": "on_change",
    "analog_gauge": "continuous",
    "bool_presence": "continuous",
    "counter": "continuous",
    "skip": "continuous",
}

# Domain-specific defaults (template strings for downstream display/tooling).
DOMAIN_SITE_MAP: dict[str, dict[str, str]] = {
    "bms_classrooms": {
        "site_id": "ies_simarro",
        "namespace": "captia",
        "entity_id_tag": "aula_id",
        "pvn_template": "{aula_id}__{variable}",
        "pvp_template": "{namespace}/{modo}/{schema_version}/{site_id}/{aula_id}/{variable}",
        "display_name_template": "{aula_id} - {variable_display}",
    },
}

# Display names ES (fallback to title-cased name).
DISPLAY_NAMES_ES: dict[str, str] = {
    # Vendor names
    "temperature": "Temperatura", "humidity": "Humedad", "co2": "CO₂",
    "iaq_index": "Índice IAQ", "noise": "Ruido", "illuminance": "Iluminancia",
    "occupancy": "Ocupación", "presence_pir": "Presencia PIR",
    "outdoor_temp": "Temp. Exterior", "daylight_lux": "Luz Natural",
    "thermostat_setpoint": "Consigna Termostato", "hvac_mode": "Modo HVAC",
    "hvac_enable": "HVAC Habilitado", "heating_valve_pos": "Pos. Válvula Calef.",
    "scene_mode": "Modo Escena", "scene": "Escena",
    "relay_1": "Relé 1", "relay_2": "Relé 2", "relay_3": "Relé 3", "relay_4": "Relé 4",
    "power": "Potencia", "energy": "Energía",
    # Production names (alias canonical)
    "temperature_01": "Temperatura (canal 01)",
    "temperature_01_sp": "Consigna Temperatura (canal 01)",
    "relative-humidity": "Humedad Relativa",
    "iaq-index": "Índice IAQ",
    "avg-sound-level": "Nivel Sonoro (medio)",
    "max-sound-level": "Nivel Sonoro (máx)",
    "luminosity": "Luminosidad",
    "people-count": "Conteo de Personas",
    "power_01": "Potencia (canal 01)",
    "energy_01": "Energía (canal 01)",
    "ac_state": "Estado AC",
    "ac_control": "Control AC",
    "fan_speed_01_state": "Estado Ventilador 1",
    "fan_speed_02_state": "Estado Ventilador 2",
    "light_01_state": "Estado Luz 1",
    "light_02_state": "Estado Luz 2",
    "valve_control": "Control Válvula",
    "temperature-outdoor": "Temperatura Exterior",
    "daylight-lux": "Luz Natural (lux)",
}


def get_assets_for_domain(
    domain_id: str,
    domain_cfg: dict[str, Any],
    n_aulas_override: int | None,
) -> list[tuple[str, str]]:
    """Return [(asset_id, asset_type)] list aligned with synthetic-generator inventory."""
    if domain_id == "bms_classrooms":
        n_aulas = n_aulas_override or int(domain_cfg.get("n_aulas", 70))
        return [(f"AULA{i:02d}", "classroom") for i in range(1, n_aulas + 1)]
    raise ValueError(f"Unsupported domain: {domain_id}")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAML not found: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _escape_str(v: str) -> str:
    return v.replace('"', '\\"')


def _build_field_str(fields: dict[str, Any]) -> str:
    parts = []
    for k, v in sorted(fields.items()):
        if isinstance(v, bool):
            parts.append(f"{k}={str(v).lower()}")
        elif isinstance(v, float):
            parts.append(f"{k}={v}")
        elif isinstance(v, int):
            parts.append(f"{k}={v}i")
        else:
            parts.append(f'{k}="{_escape_str(str(v))}"')
    return ",".join(parts)


def _build_tag_str(tags: dict[str, str]) -> str:
    return ",".join(f"{k}={v}" for k, v in sorted(tags.items()) if v)


def build_variable_lines(
    domain_id: str,
    domain_cfg: dict[str, Any],
    variables_cfg: dict[str, Any],
    derivations_cfg: dict[str, Any] | None,
    captia_env: str,
    n_aulas_override: int | None,
) -> list[str]:
    """Build line-protocol for captia_point_meta — one row per (asset, variable).

    Combines TWO sources:
      1. variables.yaml `asset_types.<type>.variables` — vendor-emitted vars
         (uses `production_name:` if present, else `name`).
      2. derivations.yaml `asset_types.<type>.derivations` — derived vars
         (12 extra vars produced by AliasSinkAdapter from vendor signals).

    Both are written to the same captia_point_meta measurement so the
    catalog reflects exactly what lands in InfluxDB.
    """
    lines: list[str] = []
    site_info = DOMAIN_SITE_MAP.get(domain_id, {})
    site_id = site_info.get("site_id", "")
    entity_id_tag = site_info.get("entity_id_tag", "asset_id")
    ts_ns = int(time.time() * 1_000_000_000)

    asset_types_cfg = variables_cfg.get("asset_types", {})
    derivations_asset_types = (derivations_cfg or {}).get("asset_types", {}) or {}
    assets = get_assets_for_domain(domain_id, domain_cfg, n_aulas_override)

    for asset_id, asset_type_name in assets:
        # ---- Vendor variables (from variables.yaml) ----
        at_data = asset_types_cfg.get(asset_type_name, {})
        variables = at_data.get("variables", []) or []
        for var in variables:
            vendor_name = var.get("name", "")
            if not vendor_name:
                continue
            canonical_name = var.get("production_name") or vendor_name
            line = _build_variable_line(
                domain_id=domain_id,
                site_id=site_id,
                asset_id=asset_id,
                asset_type=asset_type_name,
                captia_env=captia_env,
                canonical_name=canonical_name,
                vendor_name=vendor_name,
                var_cfg=var,
                entity_id_tag=entity_id_tag,
                ts_ns=ts_ns,
                source="vendor",
            )
            lines.append(line)

        # ---- Derivation variables (from derivations.yaml) ----
        deriv_data = derivations_asset_types.get(asset_type_name, {})
        derivations = deriv_data.get("derivations", []) or []
        for d in derivations:
            d_name = d.get("name", "")
            if not d_name:
                continue
            d_meta = d.get("metadata", {}) or {}
            line = _build_variable_line(
                domain_id=domain_id,
                site_id=site_id,
                asset_id=asset_id,
                asset_type=asset_type_name,
                captia_env=captia_env,
                canonical_name=d_name,
                vendor_name=d.get("source", ""),
                var_cfg=d_meta,
                entity_id_tag=entity_id_tag,
                ts_ns=ts_ns,
                source=f"derivation:{d.get('transform', 'passthrough')}",
            )
            lines.append(line)

    return lines


def _build_variable_line(
    *,
    domain_id: str,
    site_id: str,
    asset_id: str,
    asset_type: str,
    captia_env: str,
    canonical_name: str,
    vendor_name: str,
    var_cfg: dict[str, Any],
    entity_id_tag: str,
    ts_ns: int,
    source: str,
) -> str:
    """Build a single line-protocol record for captia_point_meta."""
    tags = {
        "domain_id": domain_id,
        "site_id": site_id,
        "asset_id": asset_id,
        "variable": canonical_name,
        "captia_env": captia_env,
        "asset_type": asset_type,
    }
    tag_str = _build_tag_str(tags)

    metric_kind = var_cfg.get("metric_kind", "analog_gauge")
    storage_mode = var_cfg.get("storage_mode") or _METRIC_KIND_STORAGE_MAP.get(
        metric_kind, "continuous"
    )
    rng = var_cfg.get("range", [])
    display_name = var_cfg.get(
        "display_name",
        DISPLAY_NAMES_ES.get(
            canonical_name,
            DISPLAY_NAMES_ES.get(vendor_name, canonical_name.replace("_", " ").title()),
        ),
    )

    fields: dict[str, Any] = {
        "vendor_name": vendor_name,
        "data_type": var_cfg.get("data_type", "float"),
        "unit": var_cfg.get("unit", ""),
        "category": var_cfg.get("category", "OTHER"),
        "point_type": var_cfg.get("point_type", "sensor"),
        "metric_kind": metric_kind,
        "storage_mode": storage_mode,
        "is_actuator": var_cfg.get("point_type", "") in ("actuator", "setpoint"),
        "is_optional": bool(var_cfg.get("optional", False)),
        "display_name": display_name,
        "description": var_cfg.get("description", ""),
        "entity_id_tag": entity_id_tag,
        "schema_version": "1.0",
        "updated_by": "metadata-bootstrap",
        "source": source,
    }
    if isinstance(rng, list) and len(rng) >= 1 and isinstance(rng[0], (int, float)):
        fields["range_min"] = float(rng[0])
    if isinstance(rng, list) and len(rng) >= 2 and isinstance(rng[1], (int, float)):
        fields["range_max"] = float(rng[1])

    return f"{VARIABLE_MEASUREMENT},{tag_str} {_build_field_str(fields)} {ts_ns}"


def build_domain_line(domain_id: str, domain_cfg: dict[str, Any], captia_env: str) -> str:
    site_info = DOMAIN_SITE_MAP.get(domain_id, {})
    domain_block = domain_cfg.get("domain", {})

    tags = {
        "domain_id": domain_id,
        "site_id": site_info.get("site_id", ""),
        "captia_env": captia_env,
    }
    fields: dict[str, Any] = {
        "domain_name": domain_block.get("name", domain_id),
        "namespace": site_info.get("namespace", domain_id),
        "modo_default": "synthetic",
        "schema_version": "v1.0",
        "entity_id_tag": site_info.get("entity_id_tag", "asset_id"),
        "pvn_template": site_info.get("pvn_template", "{entity_id}__{variable}"),
        "pvp_template": site_info.get("pvp_template", ""),
        "display_name_template": site_info.get("display_name_template", ""),
        "bucket": "telemetry",
        "measurement_strategy": "per_variable",
    }
    ts_ns = int(time.time() * 1_000_000_000)
    return f"{DOMAIN_MEASUREMENT},{_build_tag_str(tags)} {_build_field_str(fields)} {ts_ns}"


WRITE_BATCH_SIZE = 200
WRITE_TIMEOUT_MS = 30_000


def connect_with_retry(
    url: str, token: str, org: str, max_attempts: int = 6, delay_sec: float = 5.0
) -> InfluxDBClient:
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            client = InfluxDBClient(url=url, token=token, org=org, timeout=WRITE_TIMEOUT_MS)
            client.buckets_api().find_buckets()
            logger.info("Connected to InfluxDB on attempt %d/%d", attempt, max_attempts)
            return client
        except Exception as e:
            last_err = e
            logger.warning("Attempt %d/%d failed: %s", attempt, max_attempts, e)
            if attempt < max_attempts:
                time.sleep(delay_sec)
    raise last_err  # type: ignore[misc]


def ensure_bucket(client: InfluxDBClient, org: str) -> None:
    bapi = client.buckets_api()
    if bapi.find_bucket_by_name(METADATA_BUCKET):
        logger.info("Bucket '%s' already exists", METADATA_BUCKET)
        return
    orgs = client.organizations_api().find_organizations(org=org)
    if not orgs:
        logger.error("Org '%s' not found", org)
        sys.exit(1)
    from influxdb_client.domain.bucket_retention_rules import BucketRetentionRules
    bapi.create_bucket(
        bucket_name=METADATA_BUCKET,
        org_id=orgs[0].id,
        retention_rules=[BucketRetentionRules(type="expire", every_seconds=0)],
        description="Variable metadata catalog (aligned with telemetry)",
    )
    logger.info("Created bucket '%s' (retention=infinite)", METADATA_BUCKET)


def check_existing(client: InfluxDBClient, org: str, captia_env: str) -> bool:
    qapi = client.query_api()
    q = (
        f'from(bucket:"{METADATA_BUCKET}") |> range(start:0)'
        f' |> filter(fn:(r) => r._measurement == "{DOMAIN_MEASUREMENT}")'
        f' |> filter(fn:(r) => r.captia_env == "{captia_env}") |> limit(n:1)'
    )
    try:
        for table in qapi.query(q, org=org):
            if len(table.records) > 0:
                return True
    except Exception as e:
        logger.debug("check_existing query failed (bucket maybe empty): %s", e)
    return False


def purge_metadata(client: InfluxDBClient, org: str, domain_id: str | None = None) -> None:
    dapi = client.delete_api()
    for m in (VARIABLE_MEASUREMENT, DOMAIN_MEASUREMENT, "variable_catalog", "domain_config"):
        predicate = f'_measurement="{m}"'
        if domain_id:
            predicate += f' and domain_id="{domain_id}"'
        try:
            dapi.delete(
                start="1970-01-01T00:00:00Z",
                stop="2099-01-01T00:00:00Z",
                predicate=predicate,
                bucket=METADATA_BUCKET,
                org=org,
            )
            scope = f" (domain={domain_id})" if domain_id else ""
            logger.info("Purged measurement: %s%s", m, scope)
        except Exception as e:
            logger.debug("Could not purge %s (likely empty): %s", m, e)


def write_in_batches(write_api, bucket: str, org: str, lines: list[str]) -> int:
    written = 0
    total = len(lines)
    for i in range(0, total, WRITE_BATCH_SIZE):
        batch = lines[i : i + WRITE_BATCH_SIZE]
        write_api.write(bucket=bucket, org=org, record=batch, write_precision=WritePrecision.NS)
        written += len(batch)
        logger.info(
            "  batch %d/%d: %d lines",
            i // WRITE_BATCH_SIZE + 1,
            (total + WRITE_BATCH_SIZE - 1) // WRITE_BATCH_SIZE,
            written,
        )
    return written


def run_diagnose(args: argparse.Namespace, all_lines: list[str]) -> int:
    logger.info("=== DIAGNOSE ===")
    logger.info("  total lines to write: %d", len(all_lines))
    if all_lines:
        sample = all_lines[0][:120] + "..." if len(all_lines[0]) > 120 else all_lines[0]
        logger.info("  sample line: %s", sample)
    try:
        client = connect_with_retry(args.url, args.token, args.org, max_attempts=4, delay_sec=3.0)
    except Exception as e:
        logger.error("Connection error: %s", e)
        return 1
    try:
        ensure_bucket(client, args.org)
        if not all_lines:
            logger.error("No lines to write")
            return 1
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(
            bucket=METADATA_BUCKET, org=args.org, record=[all_lines[0]], write_precision=WritePrecision.NS
        )
        logger.info("Test write OK. Querying back...")
        qapi = client.query_api()
        q = f'from(bucket:"{METADATA_BUCKET}") |> range(start:0) |> limit(n:1)'
        count = sum(len(t.records) for t in qapi.query(q, org=args.org))
        logger.info("Read back %d record(s). DIAGNOSE OK.", count)
    except Exception as e:
        logger.error("Diagnose error: %s", e, exc_info=True)
        return 1
    finally:
        client.close()
    return 0


def main() -> int:
    logger.info("=" * 70)
    logger.info("CAPTIA-SYNTHETIC-DATA-BMS — Metadata Bootstrap")
    logger.info("=" * 70)

    p = argparse.ArgumentParser()
    p.add_argument("--url", default=os.environ.get("INFLUX_HOST", "http://influxdb:8086"))
    p.add_argument("--token", default=os.environ.get("INFLUX_TOKEN", ""))
    p.add_argument("--org", default=os.environ.get("INFLUX_ORG", "captia"))
    p.add_argument("--env", default=os.environ.get("CAPTIA_ENV", "dev"))
    p.add_argument("--domain", default=os.environ.get("BMS_DOMAIN_ID", "bms_classrooms"))
    p.add_argument("--domains-dir", default=os.environ.get("DOMAINS_DIR", "/app/domains"))
    p.add_argument("--n-aulas", type=int, default=int(os.environ.get("BMS_N_AULAS", "10")))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--purge-old", action="store_true")
    p.add_argument("--force", action="store_true", help="purge + rewrite (overrides --skip-if-exists)")
    p.add_argument("--skip-if-exists", action="store_true", help="exit 0 if metadata already present (default in deploy)")
    p.add_argument("--diagnose", action="store_true")
    args = p.parse_args()

    if not args.token:
        logger.error("Missing INFLUX_TOKEN / --token")
        return 1

    domains_dir = Path(args.domains_dir)
    if not domains_dir.exists():
        logger.error("Domains dir not found: %s", domains_dir)
        return 1

    domain_dir = domains_dir / args.domain
    if not domain_dir.exists():
        logger.error("Domain dir not found: %s", domain_dir)
        return 1

    logger.info("Domain: %s | env: %s | n_aulas: %d", args.domain, args.env, args.n_aulas)

    try:
        domain_cfg = load_yaml(domain_dir / "domain.yaml")
        variables_cfg = load_yaml(domain_dir / "variables.yaml")
    except FileNotFoundError as e:
        logger.error("YAML missing: %s", e)
        return 1
    except yaml.YAMLError as e:
        logger.error("Invalid YAML: %s", e)
        return 1

    # derivations.yaml is OPTIONAL — back-compat with deployments without it.
    derivations_path = domain_dir / "derivations.yaml"
    derivations_cfg: dict[str, Any] | None = None
    if derivations_path.exists():
        try:
            derivations_cfg = load_yaml(derivations_path)
        except yaml.YAMLError as e:
            logger.warning("derivations.yaml invalid (skipping): %s", e)
            derivations_cfg = None

    all_lines: list[str] = [build_domain_line(args.domain, domain_cfg, args.env)]
    var_lines = build_variable_lines(
        args.domain, domain_cfg, variables_cfg, derivations_cfg, args.env, args.n_aulas
    )
    all_lines.extend(var_lines)

    n_vendor = sum(
        len((variables_cfg.get("asset_types", {}).get(at, {}) or {}).get("variables", []) or [])
        for at in (variables_cfg.get("asset_types") or {})
    )
    n_derived = (
        sum(
            len((derivations_cfg.get("asset_types", {}).get(at, {}) or {}).get("derivations", []) or [])
            for at in (derivations_cfg.get("asset_types") or {})
        )
        if derivations_cfg
        else 0
    )
    logger.info(
        "Built: 1 captia_domain_meta + %d captia_point_meta = %d lines "
        "(per asset: %d vendor + %d derived = %d vars × %d aulas)",
        len(var_lines), len(all_lines), n_vendor, n_derived, n_vendor + n_derived, args.n_aulas,
    )

    if args.dry_run:
        logger.info("=== DRY RUN ===")
        for line in all_lines:
            print(line)
        logger.info("=== DRY RUN end (nothing written) ===")
        return 0

    if args.diagnose:
        return run_diagnose(args, all_lines)

    try:
        client = connect_with_retry(args.url, args.token, args.org)
    except Exception as e:
        logger.error("Connection failed: %s", e)
        return 1

    try:
        ensure_bucket(client, args.org)
    except Exception as e:
        logger.error("Bucket creation failed: %s", e)
        client.close()
        return 1

    if not args.force and not args.purge_old:
        if check_existing(client, args.org, args.env):
            if args.skip_if_exists:
                logger.info("✓ Metadata already exists for env='%s'. Skip.", args.env)
                client.close()
                return 0
            logger.warning("⚠ Metadata exists for env='%s'. Will write duplicates (use --force).", args.env)

    if args.force or args.purge_old:
        try:
            purge_metadata(client, args.org, args.domain)
        except Exception as e:
            logger.warning("Purge failed (continuing): %s", e)

    logger.info("Writing %d lines to bucket='%s' org='%s'...", len(all_lines), METADATA_BUCKET, args.org)
    try:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        n = write_in_batches(write_api, METADATA_BUCKET, args.org, all_lines)
        logger.info("✓ Wrote %d points to '%s'", n, METADATA_BUCKET)
    except Exception as e:
        logger.error("Write failed: %s", e)
        client.close()
        return 1
    finally:
        client.close()

    logger.info("=" * 70)
    logger.info("✓ Bootstrap completed")
    logger.info("=" * 70)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(130)
    except Exception as e:
        logger.error("FATAL: %s", e, exc_info=True)
        sys.exit(1)
