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
        [(e.fault_type.value, e.start.isoformat(), round(e.severity, 6)) for e in events]
    ).encode()
    digest = hashlib.sha256(payload).hexdigest()
    # Anchor digest registrado en primera ejecución (seed=42 + cfg fija).
    expected = "de6c4e491fa9c3745f67bb0e2d5f93945c654081f1ccb1b7d39cacc14b56ae66"
    assert digest == expected, f"snapshot drift: got {digest}"
