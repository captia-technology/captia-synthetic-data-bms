import hashlib
from datetime import datetime, timedelta

import numpy as np
import pytest

from bms_calibration.faults import FaultInjector


@pytest.mark.snapshot
def test_fault_injector_snapshot_seed_42() -> None:
    cfg = {
        "valve_stuck": {"probability_per_day": 0.5, "duration_minutes": 30},
    }
    injector = FaultInjector(rng=np.random.default_rng(42), config=cfg, seed=42)
    start = datetime(2025, 9, 15)
    timestamps = [start + timedelta(seconds=5 * i) for i in range(2000)]
    events = list(injector.inject(timestamps, asset_id="AULA01"))
    payload = repr(
        [
            (e.fault_type.value, e.start.isoformat(), round(e.severity, 6))
            for e in events
        ]
    ).encode()
    digest = hashlib.sha256(payload).hexdigest()
    # Anchor digest registrado tras primera ejecución; cualquier cambio rompe snapshot.
    expected = "PENDING_FIRST_RUN"
    if expected == "PENDING_FIRST_RUN":
        # Imprimir digest para registrar y luego sustituir el placeholder.
        pytest.skip(f"Snapshot anchor not set yet. Computed digest: {digest}")
    assert digest == expected, f"snapshot drift: got {digest}"
