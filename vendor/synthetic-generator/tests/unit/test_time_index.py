"""Unit tests for time index utilities."""
import pandas as pd
import pytest

from synthetic_generator.core.time_index import (
    build_time_index,
    get_day_of_week,
    get_day_of_year,
    get_dt_minutes,
    get_dt_seconds,
    get_hour_of_day,
)


class TestBuildTimeIndex:
    def test_basic(self):
        idx = build_time_index("2026-01-01", "2026-01-02", "1h")
        assert isinstance(idx, pd.DatetimeIndex)
        assert len(idx) == 25  # 24h + inclusive end

    def test_5min_freq(self):
        idx = build_time_index("2026-01-01", "2026-01-01 23:55", "5min", "Europe/Madrid")
        assert len(idx) == 288

    def test_timezone(self):
        idx = build_time_index("2026-01-01", "2026-01-01 01:00", "1h", "Europe/Madrid")
        assert str(idx.tz) == "Europe/Madrid"


class TestTemporalFeatures:
    @pytest.fixture
    def idx(self):
        return build_time_index("2026-01-01", "2026-01-01 23:55", "5min")

    def test_dt_seconds(self, idx):
        secs = get_dt_seconds(idx)
        assert float(secs[0]) == 0.0
        assert float(secs[1]) == 300.0  # 5 min

    def test_dt_minutes(self, idx):
        mins = get_dt_minutes(idx)
        assert float(mins[0]) == 0.0
        assert float(mins[1]) == 5.0

    def test_hour_of_day(self, idx):
        hours = get_hour_of_day(idx)
        assert int(hours.iloc[0]) == 0
        assert 0 <= hours.max() <= 23

    def test_day_of_week(self, idx):
        dow = get_day_of_week(idx)
        assert all(0 <= d <= 6 for d in dow.unique())

    def test_day_of_year(self, idx):
        doy = get_day_of_year(idx)
        assert int(doy.iloc[0]) == 1  # Jan 1st
