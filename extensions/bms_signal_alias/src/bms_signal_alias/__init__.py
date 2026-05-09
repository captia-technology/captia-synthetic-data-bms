"""bms_signal_alias — renombra variables vendor → producción al emit."""

from .alias_sink import AliasSinkAdapter, build_alias_map_from_yaml

__all__ = [
    "AliasSinkAdapter",
    "build_alias_map_from_yaml",
]
