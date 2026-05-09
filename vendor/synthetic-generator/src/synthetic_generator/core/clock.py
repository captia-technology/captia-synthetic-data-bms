"""Clock abstraction for testable time operations."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Protocol


class ClockPort(Protocol):
    """Port for time operations."""
    def now(self) -> datetime: ...
    def sleep(self, seconds: float) -> None: ...


class SystemClock:
    """Real system clock."""
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


class FakeClock:
    """Controllable clock for testing."""
    def __init__(self, start: datetime | None = None):
        self._now = start or datetime(2026, 1, 1, tzinfo=timezone.utc)
        self._sleep_calls: list[float] = []

    def now(self) -> datetime:
        return self._now

    def sleep(self, seconds: float) -> None:
        self._sleep_calls.append(seconds)

    def advance(self, seconds: float) -> None:
        from datetime import timedelta
        self._now += timedelta(seconds=seconds)

    @property
    def sleep_calls(self) -> list[float]:
        return list(self._sleep_calls)
