"""AliasSinkAdapter — wrapper que renombra y DERIVA variables vendor → producción.

Dos responsabilidades:
1. **Rename**: usa ``production_name`` en ``variables.yaml`` para construir
   el mapping ``vendor_name → production_name`` y renombrar cada DataPoint.
2. **Derive**: usa ``derivations.yaml`` para generar 0+ DataPoints derivados
   por cada DataPoint original (ej. ``temperature`` → ``temperature-indoor``
   con jitter, ``co2`` → ``t-voc`` con transform lineal).

Cierra L-PV-01 completamente — los DataPoints emitidos a MQTT/file/Influx
llevan los nombres canónicos de simarro-prod (21 vars rename + 12 vars
derived = 33 vars en total), drop-in replacement de telemetría real.

Cross-ref:
    docs/specs/digital-twin-bms-physics-validation/11-production-signal-mapping.md
    docs/specs/digital-twin-bms-physics-validation/07-validator-design.md
    config/domains/bms_classrooms/derivations.yaml
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from .derivations import Derivation, derive_points, load_derivations_yaml

LOG = logging.getLogger("bms_signal_alias")


def build_alias_map_from_yaml(yaml_path: Path) -> dict[str, str]:
    """Construye el dict ``{vendor_name: production_name}`` desde variables.yaml.

    Solo incluye entries donde ``production_name`` está definido y difiere de
    ``name``. Si la entry no tiene ``production_name`` o ambos son iguales,
    se omite del mapping (passthrough).

    Soporta formato vendor (``asset_types: <type>: variables: [...]``).
    """
    if not yaml_path.exists():
        LOG.warning("variables.yaml not found at %s — alias map empty", yaml_path)
        return {}

    with yaml_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    aliases: dict[str, str] = {}
    asset_types = data.get("asset_types") or {}
    if not isinstance(asset_types, dict):
        return aliases

    for _asset_type, asset_def in asset_types.items():
        if not isinstance(asset_def, dict):
            continue
        for var in asset_def.get("variables", []) or []:
            if not isinstance(var, dict):
                continue
            name = var.get("name")
            prod_name = var.get("production_name")
            if not name or not prod_name:
                continue
            if name != prod_name:
                aliases[name] = prod_name
    return aliases


class AliasSinkAdapter:
    """Sink wrapper que renombra ``DataPoint.variable`` antes de emit.

    Conforma con ``SinkAdapterPort`` (Protocol) del vendor expuesto en
    ``synthetic_generator.ports``: implementa ``open``, ``close``, ``emit``,
    ``emit_batch``, ``flush``. Si el sink envuelto no tiene alguno de estos
    métodos, el adapter actúa como no-op para esa operación.

    El adapter NO muta los DataPoints originales: usa ``dataclasses.replace``
    para crear copias renombradas y los pasa al sink real.

    Args:
        real_sink: instancia que implementa ``SinkAdapterPort``.
        aliases: dict ``{vendor_name: production_name}``. Variables no
                 presentes en el dict pasan sin renombrar.
    """

    def __init__(
        self,
        real_sink: Any,
        aliases: dict[str, str],
        derivations: dict[str, list[Derivation]] | None = None,
    ):
        self.real_sink = real_sink
        self.aliases = dict(aliases)
        self.derivations = dict(derivations or {})
        self._renamed_count = 0
        self._passthrough_count = 0
        self._derived_count = 0
        n_derivations = sum(len(v) for v in self.derivations.values())
        LOG.info(
            "AliasSinkAdapter wrapping %s with %d alias entries + %d derivations",
            type(real_sink).__name__,
            len(self.aliases),
            n_derivations,
        )

    @classmethod
    def from_yaml(
        cls, real_sink: Any, yaml_path: Path, derivations_yaml: Path | None = None
    ) -> AliasSinkAdapter:
        """Construye el adapter cargando alias map + derivations desde YAMLs."""
        aliases = build_alias_map_from_yaml(yaml_path)
        derivations = load_derivations_yaml(derivations_yaml) if derivations_yaml else {}
        return cls(real_sink, aliases, derivations)

    @property
    def renamed_count(self) -> int:
        return self._renamed_count

    @property
    def passthrough_count(self) -> int:
        return self._passthrough_count

    @property
    def derived_count(self) -> int:
        return self._derived_count

    def open(self) -> None:
        if hasattr(self.real_sink, "open"):
            self.real_sink.open()

    def close(self) -> None:
        if hasattr(self.real_sink, "close"):
            self.real_sink.close()

    def flush(self) -> None:
        if hasattr(self.real_sink, "flush"):
            self.real_sink.flush()

    def emit(self, point: Any) -> Any:
        """Emit ORIGINAL (renamed) + DERIVED points to the real sink.

        Order: derivations are computed BEFORE rename so they match against
        vendor names (e.g. derivation source="temperature" matches before
        the point gets renamed to "temperature_01").
        """
        derived = derive_points(point, self.derivations)
        result = self.real_sink.emit(self._rename(point))
        for d in derived:
            self.real_sink.emit(self._rename(d))
            self._derived_count += 1
        return result

    def emit_batch(self, points: Iterable[Any]) -> int:
        """Emit batch with derivations interleaved.

        BUG FIX (audit E2E):
          - vendor FileSinkAdapter.emit_batch llama len(points) → falla con generator.
            Materializamos a list para preservar compatibilidad con Sequence-based sinks.
          - vendor ScenarioRunner.run_backfill hace `result.points_emitted += sink.emit_batch(batch)`.
            emit_batch DEBE retornar int (cuenta de puntos emitidos). Forward return.

        Derivations: por cada point original, expandimos a [point + derived...]
        ANTES de renombrar (para que `source` matchee vendor names).
        """
        expanded: list[Any] = []
        for p in points:
            expanded.append(p)
            extras = derive_points(p, self.derivations)
            expanded.extend(extras)
            self._derived_count += len(extras)

        renamed = [self._rename(p) for p in expanded]
        if hasattr(self.real_sink, "emit_batch"):
            n = self.real_sink.emit_batch(renamed)
            return n if n is not None else len(renamed)
        else:
            for p in renamed:
                self.real_sink.emit(p)
            return len(renamed)

    def _rename(self, point: Any) -> Any:
        """Rename ``point.variable`` if in alias map; else passthrough.

        Uses ``dataclasses.replace`` to avoid mutating the original.
        Falls back to attribute reassignment for non-dataclass points.
        """
        old_name = getattr(point, "variable", None)
        new_name = self.aliases.get(old_name) if old_name else None
        if new_name is None or new_name == old_name:
            self._passthrough_count += 1
            return point

        self._renamed_count += 1
        try:
            return replace(point, variable=new_name)
        except TypeError:
            # Not a dataclass — try attribute assignment on a copy.
            import copy

            clone = copy.copy(point)
            clone.variable = new_name
            return clone
