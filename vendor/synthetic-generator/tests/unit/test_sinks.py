"""Unit tests for sink adapters."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from synthetic_generator.core.models import DataPoint, DataType, PointType, Quality
from synthetic_generator.sinks.file import FileSinkAdapter, FileSinkConfig
from synthetic_generator.sinks.stdout import StdoutSinkAdapter
from synthetic_generator.sinks.null import NullSink
from synthetic_generator.sinks.composite import CompositeSink


def _make_point(value=22.5, variable="temperature") -> DataPoint:
    return DataPoint(
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        domain_id="test",
        site_id="site",
        asset_id="ASSET01",
        variable=variable,
        value=value,
        unit="°C",
        data_type=DataType.FLOAT,
        point_type=PointType.SENSOR,
        quality=Quality.OK,
        origin="synthetic",
        pvn="ASSET01__temperature",
    )


class TestNullSink:
    def test_emit(self):
        sink = NullSink()
        sink.open()
        sink.emit(_make_point())
        assert sink.emitted_count == 1
        sink.close()

    def test_emit_batch(self):
        sink = NullSink()
        sink.open()
        count = sink.emit_batch([_make_point(), _make_point()])
        assert count == 2
        assert sink.emitted_count == 2
        sink.close()

    def test_name(self):
        assert NullSink().name == "null"


class TestStdoutSink:
    def test_emit(self, capsys):
        sink = StdoutSinkAdapter()
        sink.open()
        sink.emit(_make_point())
        captured = capsys.readouterr()
        assert '"value": 22.5' in captured.out
        assert "ASSET01" in captured.out
        assert "temperature" in captured.out
        sink.close()

    def test_emit_string_value(self, capsys):
        """String values are skipped (can't store as float in captia_point)."""
        sink = StdoutSinkAdapter()
        sink.open()
        sink.emit(_make_point(value="on"))
        captured = capsys.readouterr()
        assert captured.out == ""
        sink.close()

    def test_none_value_skipped(self, capsys):
        sink = StdoutSinkAdapter()
        sink.open()
        sink.emit(_make_point(value=None))
        captured = capsys.readouterr()
        assert captured.out == ""
        sink.close()

    def test_name(self):
        assert StdoutSinkAdapter().name == "stdout"


class TestFileSink:
    def test_csv_long(self, tmp_path):
        path = str(tmp_path / "out.csv")
        sink = FileSinkAdapter(FileSinkConfig(path=path, format="csv_long"))
        sink.open()
        sink.emit(_make_point())
        sink.emit(_make_point(value=23.0))
        sink.close()

        content = Path(path).read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows
        assert "timestamp" in lines[0]
        assert "ASSET01" in lines[1]

    def test_jsonl(self, tmp_path):
        path = str(tmp_path / "out.jsonl")
        sink = FileSinkAdapter(FileSinkConfig(path=path, format="jsonl"))
        sink.open()
        sink.emit(_make_point())
        sink.close()

        content = Path(path).read_text(encoding="utf-8")
        record = json.loads(content.strip())
        assert record["asset_id"] == "ASSET01"
        assert record["variable"] == "temperature"

    def test_csv_wide(self, tmp_path):
        path = str(tmp_path / "wide.csv")
        sink = FileSinkAdapter(FileSinkConfig(path=path, format="csv_wide"))
        sink.open()
        sink.emit(_make_point(value=22.5, variable="temperature"))
        sink.emit(_make_point(value=55.0, variable="humidity"))
        sink.close()

        content = Path(path).read_text(encoding="utf-8")
        assert "temperature" in content or "humidity" in content

    def test_name(self):
        assert FileSinkAdapter(FileSinkConfig()).name == "file"

    def test_creates_directories(self, tmp_path):
        path = str(tmp_path / "deep" / "nested" / "out.csv")
        sink = FileSinkAdapter(FileSinkConfig(path=path))
        sink.open()
        sink.emit(_make_point())
        sink.close()
        assert Path(path).exists()


class TestCompositeSink:
    def test_fan_out(self):
        null1 = NullSink()
        null2 = NullSink()
        composite = CompositeSink([null1, null2])
        composite.open()
        composite.emit(_make_point())
        composite.close()
        assert null1.emitted_count == 1
        assert null2.emitted_count == 1

    def test_emit_batch(self):
        null1 = NullSink()
        null2 = NullSink()
        composite = CompositeSink([null1, null2])
        composite.open()
        count = composite.emit_batch([_make_point(), _make_point()])
        composite.close()
        assert count == 2
        assert null1.emitted_count == 2

    def test_name(self):
        sink = CompositeSink([NullSink(), NullSink()])
        assert "composite" in sink.name
        assert "null" in sink.name

    def test_error_isolation(self):
        """One sink error should not prevent others from receiving data."""
        class BadSink:
            name = "bad"
            def open(self): pass
            def emit(self, p): raise RuntimeError("fail")
            def emit_batch(self, ps): raise RuntimeError("fail")
            def flush(self): pass
            def close(self): pass

        null = NullSink()
        composite = CompositeSink([BadSink(), null])
        composite.open()
        composite.emit(_make_point())
        composite.close()
        assert null.emitted_count == 1
