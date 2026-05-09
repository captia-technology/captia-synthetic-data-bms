"""Unit tests for clock abstraction."""
from datetime import datetime, timezone, timedelta

from synthetic_generator.core.clock import FakeClock, SystemClock


class TestSystemClock:
    def test_now_returns_datetime(self):
        c = SystemClock()
        now = c.now()
        assert isinstance(now, datetime)
        assert now.tzinfo is not None


class TestFakeClock:
    def test_default_start(self):
        c = FakeClock()
        assert c.now().year == 2026

    def test_custom_start(self):
        start = datetime(2025, 6, 15, 12, 0, tzinfo=timezone.utc)
        c = FakeClock(start=start)
        assert c.now() == start

    def test_advance(self):
        c = FakeClock()
        t0 = c.now()
        c.advance(60.0)
        t1 = c.now()
        assert (t1 - t0).total_seconds() == 60.0

    def test_sleep_records(self):
        c = FakeClock()
        assert c.sleep_calls == []
        c.sleep(0.5)
        c.sleep(1.0)
        assert c.sleep_calls == [0.5, 1.0]

    def test_sleep_does_not_advance(self):
        c = FakeClock()
        t0 = c.now()
        c.sleep(10.0)
        assert c.now() == t0
