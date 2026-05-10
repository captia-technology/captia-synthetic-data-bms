"""bms_signal_alias — renombra y deriva variables vendor → producción al emit."""

from .alias_sink import AliasSinkAdapter, build_alias_map_from_yaml
from .derivations import (
    Derivation,
    derive_iterable,
    derive_points,
    load_derivations_yaml,
)

__all__ = [
    "AliasSinkAdapter",
    "Derivation",
    "build_alias_map_from_yaml",
    "derive_iterable",
    "derive_points",
    "load_derivations_yaml",
]
