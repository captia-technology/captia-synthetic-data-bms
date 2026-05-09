import pytest

from bms_data_generator.metrics import (
    metrics_text,
    record_fault,
    record_points,
    record_publish,
    record_publish_error,
)


@pytest.mark.unit
def test_record_publish_increments() -> None:
    record_publish(topic="captia/dev/default/ies_simarro/AULA01/telemetry/co2", count=5)
    text = metrics_text().decode()
    assert "captia_bms_messages_published_total" in text


@pytest.mark.unit
def test_record_fault_appears_in_metrics() -> None:
    record_fault(fault_type="valve_stuck")
    text = metrics_text().decode()
    assert "captia_bms_faults_injected_total" in text
    assert 'fault_type="valve_stuck"' in text


@pytest.mark.unit
def test_record_publish_error_appears() -> None:
    record_publish_error(
        topic="captia/dev/default/ies_simarro/AULA01/telemetry/co2", reason="timeout"
    )
    text = metrics_text().decode()
    assert "captia_bms_publish_errors_total" in text


@pytest.mark.unit
def test_record_points_appears() -> None:
    record_points(domain="bms_classrooms", asset="AULA01", count=42)
    text = metrics_text().decode()
    assert "captia_bms_points_generated_total" in text
