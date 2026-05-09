# Synthetic Data Generator (vendored, BMS-only)

> Vendored snapshot for **CAPTIA-SYNTHETIC-DATA-BMS**. This build only ships the
> `bms_classrooms` domain. See `PATCHES/001-bms-only.patch` and `VENDOR.md`.

Hexagonal architecture (`core` / `ports` / `domains` / `sinks`) for deterministic
time-series data generation. Read-only from the parent repo: extensions go in
`extensions/bms_calibration/` and `modules/bms-data-generator/`.

## Quickstart

```bash
# From the parent workspace root
uv sync

# List domains (only bms_classrooms in this build)
uv run python -c "
from synthetic_generator.domains.registry import auto_discover_domains, list_domain_info
auto_discover_domains()
for info in list_domain_info():
    print(f\"  {info['domain_id']}: {info['description']}\")
"
```

## Usage

### File sink (CSV / JSONL)

```python
from synthetic_generator.core.config import (
    DomainReference, ProjectConfig, ScenarioConfig, SimulationConfig, SinkConfig, SinkType,
)
from synthetic_generator.core.runner import ScenarioRunner
from synthetic_generator.core.validator import ContractValidator
from synthetic_generator.domains.registry import auto_discover_domains, get_domain
from synthetic_generator.sinks.file import FileSinkAdapter, FileSinkConfig

auto_discover_domains()
domain = get_domain("bms_classrooms")

config = ScenarioConfig(
    project=ProjectConfig(namespace="captia", site_id="ies_simarro"),
    simulation=SimulationConfig(start="2026-01-01", end="2026-01-07", freq="5min", seed=42),
    domain=DomainReference(id="bms_classrooms"),
    sinks=[SinkConfig(type=SinkType.FILE, config={"path": "outputs/data.jsonl", "format": "jsonl"})],
)
sink = FileSinkAdapter(FileSinkConfig(path="outputs/data.jsonl", format="jsonl"))
runner = ScenarioRunner(config, domain, sink, validator=ContractValidator())
results = runner.run()
```

### MQTT sink

```python
from synthetic_generator.sinks.mqtt import MQTTSinkAdapter, MQTTSinkConfig

sink = MQTTSinkAdapter(MQTTSinkConfig(broker_url="tcp://localhost:1883", captia_env="dev"))
# Wire into ScenarioRunner as above.
```

## Domain (BMS classrooms)

| Domain | Assets | Variables | Description |
|--------|--------|-----------|-------------|
| `bms_classrooms` | 1–70 aulas | 16–21 / aula | Temperature, RH, CO2, IAQ, sound, lux, occupancy, HVAC, energy |

## Architecture

```
core/           Business logic (no external deps)
  runner.py       ScenarioRunner (backfill + live)
  config.py       Pydantic v2 ScenarioConfig
  validator.py    ContractValidator (pre-emission)
  rate.py         RateController (token-bucket)
  clock.py        ClockPort + FakeClock
  anomalies.py    AnomalyEngine
ports/          Protocol interfaces
  domain.py       DomainAdapterPort
  sink.py         SinkAdapterPort
domains/        bms_classrooms (only domain in this vendor build)
sinks/          5 sink adapters (MQTT, File, Stdout, Composite, Null)
```

## Testing

Run from the parent workspace root:

```bash
uv run pytest -m unit          # Vendor unit tests
uv run pytest -m snapshot      # Determinism (seed=42)
```

## Troubleshooting

- **Import errors**: re-run `uv sync` from the parent root.
- **MQTT connection**: broker must be reachable at `tcp://localhost:1883` (or whatever `BMS_MQTT_HOST` resolves to).
- **Determinism**: always use `np.random.default_rng(seed)` (NOT `np.random.seed()`).

## References

- Parent specs: `docs/specs/synthetic-bms/`.
- Vendor governance: `vendor/synthetic-generator/VENDOR.md`.
