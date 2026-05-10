"""Derivations engine — generate extra DataPoints from vendor signals.

Closes L-PV-01 fully: the vendor `synthetic-generator` emits 21 variables;
production `simarro-prod` (PPTX slide 14) requires 12 additional variables
(temperature-indoor, t-voc, max-sound-level, aire/aire_state, fan_speed_NN,
light_NN intensities, valve_state). This module reads
`config/domains/<dom>/derivations.yaml` and applies declarative transforms
to each emitted DataPoint, spawning 0 or more extra DataPoints with the
derived `variable` name.

Wired into `AliasSinkAdapter`: each `emit(point)` becomes
`emit(point) + emit(*derivatives_of_point)`. The downstream sink (MQTT,
file, etc.) sees them as independent points indistinguishable from
vendor-native physics.

Transform catalogue:
    passthrough       → value as-is (just rename)
    jitter            → value + N(0, stddev) clipped
    linear            → a*value + b + N(0, noise_stddev) clipped
    bool_to_speed     → speed_on if value > 0.5 else speed_off, with jitter
    bool_to_intensity → intensity_on if value > 0.5 else intensity_off, with jitter
    threshold_to_bool → 1.0 if value > threshold else 0.0

All transforms are deterministic given the same seed (use `numpy.random.default_rng`
or accept rng parameter; default uses `np.random.default_rng(seed=hash(name))`
so values vary per-variable but stay reproducible).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml

LOG = logging.getLogger("bms_signal_alias.derivations")


@dataclass
class Derivation:
    """One derivation rule loaded from derivations.yaml."""

    name: str
    source: str
    transform: str
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


# ────────────────────────────── Transforms ──────────────────────────────


def _clip(value: float, params: dict[str, Any]) -> float:
    cmin = params.get("clip_min")
    cmax = params.get("clip_max")
    if cmin is not None:
        value = max(value, float(cmin))
    if cmax is not None:
        value = min(value, float(cmax))
    return value


def transform_passthrough(value: float, params: dict[str, Any], rng: np.random.Generator) -> float:
    return float(value)


def transform_jitter(value: float, params: dict[str, Any], rng: np.random.Generator) -> float:
    stddev = float(params.get("stddev", 0.0))
    return _clip(float(value) + float(rng.normal(0.0, stddev)), params)


def transform_linear(value: float, params: dict[str, Any], rng: np.random.Generator) -> float:
    a = float(params.get("a", 1.0))
    b = float(params.get("b", 0.0))
    noise_stddev = float(params.get("noise_stddev", 0.0))
    out = a * float(value) + b + float(rng.normal(0.0, noise_stddev))
    return _clip(out, params)


def transform_bool_to_speed(
    value: float, params: dict[str, Any], rng: np.random.Generator
) -> float:
    """When source bool is on (>0.5), output speed_on ± jitter; else speed_off."""
    speed_on = float(params.get("speed_on", 100.0))
    speed_off = float(params.get("speed_off", 0.0))
    jitter_stddev = float(params.get("jitter_stddev", 0.0))
    base = speed_on if float(value) > 0.5 else speed_off
    if jitter_stddev > 0 and base > 0:
        base += float(rng.normal(0.0, jitter_stddev))
    return _clip(base, {"clip_min": 0.0, "clip_max": params.get("clip_max", 100.0)})


def transform_bool_to_intensity(
    value: float, params: dict[str, Any], rng: np.random.Generator
) -> float:
    """Same as bool_to_speed but with intensity_on/off naming for clarity."""
    intensity_on = float(params.get("intensity_on", 100.0))
    intensity_off = float(params.get("intensity_off", 0.0))
    jitter_stddev = float(params.get("jitter_stddev", 0.0))
    base = intensity_on if float(value) > 0.5 else intensity_off
    if jitter_stddev > 0 and base > 0:
        base += float(rng.normal(0.0, jitter_stddev))
    return _clip(base, {"clip_min": 0.0, "clip_max": params.get("clip_max", 100.0)})


def transform_threshold_to_bool(
    value: float, params: dict[str, Any], rng: np.random.Generator
) -> float:
    threshold = float(params.get("threshold", 0.0))
    return 1.0 if float(value) > threshold else 0.0


_TRANSFORMS = {
    "passthrough": transform_passthrough,
    "jitter": transform_jitter,
    "linear": transform_linear,
    "bool_to_speed": transform_bool_to_speed,
    "bool_to_intensity": transform_bool_to_intensity,
    "threshold_to_bool": transform_threshold_to_bool,
}


# ────────────────────────────── Loader ──────────────────────────────


def load_derivations_yaml(yaml_path: Path) -> dict[str, list[Derivation]]:
    """Return ``{source_vendor_name: [Derivation, ...]}`` index for fast lookup.

    Multiple derivations can share the same source. Returns empty dict if
    the file does not exist (backward-compatible: alias-only setups still
    work).
    """
    if not yaml_path.exists():
        LOG.info("derivations.yaml not found at %s — derivations disabled", yaml_path)
        return {}

    with yaml_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    by_source: dict[str, list[Derivation]] = {}
    asset_types = data.get("asset_types") or {}
    if not isinstance(asset_types, dict):
        return by_source

    for _asset_type, asset_def in asset_types.items():
        if not isinstance(asset_def, dict):
            continue
        for raw in asset_def.get("derivations", []) or []:
            if not isinstance(raw, dict):
                continue
            name = raw.get("name")
            source = raw.get("source")
            transform = raw.get("transform", "passthrough")
            if not name or not source:
                LOG.warning("Skipping derivation with missing name/source: %r", raw)
                continue
            if transform not in _TRANSFORMS:
                LOG.warning(
                    "Skipping derivation %r: unknown transform %r (known: %s)",
                    name, transform, sorted(_TRANSFORMS.keys()),
                )
                continue
            d = Derivation(
                name=str(name),
                source=str(source),
                transform=str(transform),
                params=dict(raw.get("params") or {}),
                metadata=dict(raw.get("metadata") or {}),
            )
            by_source.setdefault(d.source, []).append(d)

    total = sum(len(v) for v in by_source.values())
    LOG.info(
        "Loaded %d derivations from %s, indexed by %d source vars",
        total, yaml_path, len(by_source),
    )
    return by_source


# ────────────────────────────── Engine ──────────────────────────────


def _rng_for(name: str, asset_id: str | None, ts_ns: int | None) -> np.random.Generator:
    """Deterministic RNG per (name, asset, time-bucket) so jitter is reproducible
    within a 5-second window but distinct across vars/aulas."""
    bucket = (ts_ns or 0) // 5_000_000_000  # 5 s buckets
    seed_str = f"{name}|{asset_id or ''}|{bucket}"
    seed = abs(hash(seed_str)) % (2**32)
    return np.random.default_rng(seed)


def derive_points(point: Any, derivations_by_source: dict[str, list[Derivation]]) -> list[Any]:
    """Given one DataPoint, return the list of derived DataPoints to emit.

    Returns empty list if the point's variable has no derivations registered.
    Each derived point is a `dataclasses.replace` clone with new
    `variable` name and transformed `value`.
    """
    src_var = getattr(point, "variable", None)
    if not src_var or src_var not in derivations_by_source:
        return []

    src_value = getattr(point, "value", None)
    if src_value is None or isinstance(src_value, str):
        return []

    src_value_f = float(src_value)
    asset = getattr(point, "asset_id", None)
    ts_ns = None
    ts = getattr(point, "timestamp", None)
    if ts is not None and hasattr(ts, "timestamp"):
        try:
            ts_ns = int(ts.timestamp() * 1e9)
        except Exception:
            ts_ns = None

    out: list[Any] = []
    for d in derivations_by_source[src_var]:
        rng = _rng_for(d.name, asset, ts_ns)
        try:
            new_value = _TRANSFORMS[d.transform](src_value_f, d.params, rng)
        except Exception as exc:  # noqa: BLE001
            LOG.warning("Derivation %s failed for %s: %s", d.name, src_var, exc)
            continue

        try:
            from dataclasses import replace

            new_point = replace(point, variable=d.name, value=new_value)
        except TypeError:
            import copy

            new_point = copy.copy(point)
            new_point.variable = d.name
            new_point.value = new_value
        out.append(new_point)

    return out


def derive_iterable(
    points: Iterable[Any], derivations_by_source: dict[str, list[Derivation]]
) -> Iterable[Any]:
    """Yield each input point followed by its derived points (flat stream)."""
    for p in points:
        yield p
        for d in derive_points(p, derivations_by_source):
            yield d
