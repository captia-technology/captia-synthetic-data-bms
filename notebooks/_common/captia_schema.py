"""Constantes del schema canónico CAPTIA.

Reglas vinculantes (no editar sin pasar por `docs/specs/synthetic-bms/02-domain-spec.md`):

- Measurement único: ``captia_point`` para telemetría continua.
- 5 tags indexados: ``captia_env``, ``domain_id``, ``site_id``, ``asset_id``,
  ``variable``.
- 1 field: ``value`` (float; estados booleanos como 0.0/1.0).
- Topic MQTT estructurado:
  ``captia/{env}/{tenant}/{site}/{device}/telemetry/{variable}``.
- Etiquetas de fallo Caso C en measurement separado ``captia_fault_labels``.
"""

from __future__ import annotations

from typing import Final

DEFAULT_SEED: Final[int] = 42

MEASUREMENT_TELEMETRY: Final[str] = "captia_point"
MEASUREMENT_FAULT_LABELS: Final[str] = "captia_fault_labels"
MEASUREMENT_METADATA: Final[str] = "captia_point_meta"

CANONICAL_TAGS: Final[tuple[str, ...]] = (
    "captia_env",
    "domain_id",
    "site_id",
    "asset_id",
    "variable",
)

DEFAULT_BUCKET_RETENTIONS: Final[dict[str, str]] = {
    "telemetry": "14d",
    "telemetry_1m": "30d",
    "telemetry_15m": "90d",
    "telemetry_1h": "365d",
    "state_events": "90d",
    "telemetry_events": "90d",
    "captia_metadata": "infinite",
}

# Variables canónicas v1 (subset para los notebooks). Fuente:
# docs/specs/synthetic-bms/02-domain-spec.md tabla de variables.
KNOWN_VARIABLES: Final[dict[str, dict[str, object]]] = {
    "temperature_01": {"unit": "C", "range": (16, 32), "metric_kind": "analog_gauge"},
    "relative_humidity_01": {"unit": "%RH", "range": (20, 80), "metric_kind": "analog_gauge"},
    "co2": {"unit": "ppm", "range": (300, 5000), "metric_kind": "analog_gauge"},
    "t_voc": {"unit": "ppb", "range": (0, 3000), "metric_kind": "analog_gauge"},
    "iaq_index": {"unit": "index", "range": (0, 500), "metric_kind": "analog_gauge"},
    "avg_sound_level": {"unit": "dB", "range": (30, 90), "metric_kind": "analog_gauge"},
    "max_sound_level": {"unit": "dB", "range": (30, 110), "metric_kind": "analog_gauge"},
    "luminosity": {"unit": "lux", "range": (0, 2000), "metric_kind": "analog_gauge"},
    "power_01": {"unit": "W", "range": (0, 3000), "metric_kind": "counter"},
    "temperature_supply": {"unit": "C", "range": (8, 30), "metric_kind": "analog_gauge"},
    "temperature_return": {"unit": "C", "range": (8, 32), "metric_kind": "analog_gauge"},
    "solar_irradiance": {"unit": "W/m2", "range": (0, 1100), "metric_kind": "analog_gauge"},
    "temperature_outdoor": {"unit": "C", "range": (-5, 45), "metric_kind": "analog_gauge"},
    "ac_state": {"unit": "bool", "range": (0, 1), "metric_kind": "bool_state"},
    "ac_control": {"unit": "bool", "range": (0, 1), "metric_kind": "bool_state"},
    "fan_speed_01_state": {"unit": "bool", "range": (0, 1), "metric_kind": "bool_state"},
    "fan_speed_02_state": {"unit": "bool", "range": (0, 1), "metric_kind": "bool_state"},
    "fan_speed_03_state": {"unit": "bool", "range": (0, 1), "metric_kind": "bool_state"},
    "light_01_state": {"unit": "bool", "range": (0, 1), "metric_kind": "bool_state"},
    "light_02_state": {"unit": "bool", "range": (0, 1), "metric_kind": "bool_state"},
    "valve_control": {"unit": "bool", "range": (0, 1), "metric_kind": "bool_state"},
    "valve_state": {"unit": "bool", "range": (0, 1), "metric_kind": "bool_state"},
    "occupancy": {"unit": "bool", "range": (0, 1), "metric_kind": "bool_presence"},
    "people_count": {"unit": "count", "range": (0, 50), "metric_kind": "analog_gauge"},
    "vehicle_count": {"unit": "count", "range": (0, 200), "metric_kind": "analog_gauge"},
    "wind_speed": {"unit": "m/s", "range": (0, 30), "metric_kind": "analog_gauge"},
    "precipitation": {"unit": "mm", "range": (0, 100), "metric_kind": "counter"},
    "pressure": {"unit": "hPa", "range": (950, 1050), "metric_kind": "analog_gauge"},
}


def build_topic(
    *,
    env: str,
    tenant: str,
    site: str,
    asset: str,
    variable: str,
    kind: str = "telemetry",
) -> str:
    """Construye un topic MQTT canónico.

    Ejemplo:
    >>> build_topic(env="prod", tenant="default", site="ies_simarro",
    ...             asset="AULA01", variable="co2")
    'captia/prod/default/ies_simarro/AULA01/telemetry/co2'
    """
    if kind not in {"telemetry", "event"}:
        raise ValueError(f"kind must be 'telemetry' or 'event', got {kind!r}")
    return f"captia/{env}/{tenant}/{site}/{asset}/{kind}/{variable}"


def build_line_protocol(
    *,
    measurement: str,
    tags: dict[str, str],
    fields: dict[str, float],
    timestamp_ns: int,
) -> str:
    """Construye una línea de InfluxDB line protocol válida.

    Notas:
    - Los tags se ordenan alfabéticamente (mejora compresión TSDB).
    - Field ``value`` se serializa como float ``...0.0`` para forzar tipo.
    """
    if not tags:
        raise ValueError("Line protocol requires at least one tag")
    if "value" not in fields:
        raise ValueError("CAPTIA canonical schema requires field 'value'")
    tag_str = ",".join(f"{k}={tags[k]}" for k in sorted(tags))
    field_parts: list[str] = []
    for k, v in fields.items():
        if isinstance(v, bool):
            field_parts.append(f"{k}={1 if v else 0}i")
        else:
            field_parts.append(f"{k}={float(v)}")
    field_str = ",".join(field_parts)
    return f"{measurement},{tag_str} {field_str} {timestamp_ns}"


def validate_canonical_tags(tags: dict[str, str]) -> None:
    """Lanza ValueError si faltan tags canónicos o sobran tags inesperados.

    El uso típico es validar un DataFrame antes de escribir a InfluxDB:

    >>> validate_canonical_tags({
    ...     "captia_env": "dev", "domain_id": "bms_classrooms",
    ...     "site_id": "ies_simarro", "asset_id": "AULA01",
    ...     "variable": "co2",
    ... })  # OK
    """
    missing = [t for t in CANONICAL_TAGS if t not in tags]
    if missing:
        raise ValueError(f"Missing canonical CAPTIA tags: {missing}")
    extras = sorted(set(tags) - set(CANONICAL_TAGS))
    if extras:
        # No es error duro: state_events admite tags extra como `stat`. Avisar.
        import warnings

        warnings.warn(
            f"Non-canonical tags present: {extras}. Confirma que es intencional.",
            UserWarning,
            stacklevel=2,
        )
