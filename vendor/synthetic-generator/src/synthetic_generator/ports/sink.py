"""Sink adapter port — interface for data output destinations."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..core.models import DataPoint


@runtime_checkable
class SinkAdapterPort(Protocol):
    """Port for data output destinations.

    Ref: docs/specs/core-architecture.md Section 3.2
    """

    def open(self) -> None: ...
    def emit(self, point: DataPoint) -> None: ...
    def emit_batch(self, points: list[DataPoint]) -> int: ...
    def flush(self) -> None: ...
    def close(self) -> None: ...

    @property
    def name(self) -> str: ...
