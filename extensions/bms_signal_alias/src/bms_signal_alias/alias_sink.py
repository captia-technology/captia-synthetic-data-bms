"""AliasSinkAdapter — wrapper que renombra variables vendor → producción.

Usa el campo opcional ``production_name`` por entry en
``config/domains/<domain>/variables.yaml`` para construir el mapping
``vendor_name → production_name``. Aplica el rename a cada DataPoint antes
de delegar al sink real.

Cierra L-PV-01 (parcialmente) — los DataPoints emitidos a MQTT/file/Influx
llevan los nombres canónicos de simarro-prod, lo que hace al generador
sintético drop-in replacement de telemetría real.

Cross-ref:
    docs/specs/digital-twin-bms-physics-validation/11-production-signal-mapping.md
    docs/specs/digital-twin-bms-physics-validation/07-validator-design.md
"""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

import yaml

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

    def __init__(self, real_sink: Any, aliases: dict[str, str]):
        self.real_sink = real_sink
        self.aliases = dict(aliases)
        self._renamed_count = 0
        self._passthrough_count = 0
        LOG.info("AliasSinkAdapter wrapping %s with %d alias entries",
                 type(real_sink).__name__, len(self.aliases))

    @classmethod
    def from_yaml(cls, real_sink: Any, yaml_path: Path) -> "AliasSinkAdapter":
        """Construye el adapter cargando el mapping desde un fichero YAML."""
        aliases = build_alias_map_from_yaml(yaml_path)
        return cls(real_sink, aliases)

    @property
    def renamed_count(self) -> int:
        return self._renamed_count

    @property
    def passthrough_count(self) -> int:
        return self._passthrough_count

    def open(self) -> None:
        if hasattr(self.real_sink, "open"):
            self.real_sink.open()

    def close(self) -> None:
        if hasattr(self.real_sink, "close"):
            self.real_sink.close()

    def flush(self) -> None:
        if hasattr(self.real_sink, "flush"):
            self.real_sink.flush()

    def emit(self, point: Any) -> None:
        self.real_sink.emit(self._rename(point))

    def emit_batch(self, points: Iterable[Any]) -> None:
        renamed = (self._rename(p) for p in points)
        if hasattr(self.real_sink, "emit_batch"):
            self.real_sink.emit_batch(renamed)
        else:
            for p in renamed:
                self.real_sink.emit(p)

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
