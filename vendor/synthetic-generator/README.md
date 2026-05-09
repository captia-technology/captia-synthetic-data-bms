# Synthetic Data Generator

Modular, multi-domain synthetic data generator for CAPTIA-connect. Generates deterministic time-series data using hexagonal architecture with pluggable domain and sink adapters.

## Quickstart

```bash
# Install
cd tools/synthetic-generator
uv sync

# Run tests
uv run python -m pytest tests/ -v

# List available domains
uv run python -c "
from synthetic_generator.domains.registry import auto_discover_domains, list_domain_info
auto_discover_domains()
for info in list_domain_info():
    print(f\"  {info['domain_id']}: {info['description']}\")
"
```

## Usage

### File Sink (CSV/JSONL)

```python
from synthetic_generator.core.config import *
from synthetic_generator.core.runner import ScenarioRunner
from synthetic_generator.core.validator import ContractValidator
from synthetic_generator.domains.registry import auto_discover_domains, get_domain
from synthetic_generator.sinks.file import FileSinkAdapter, FileSinkConfig

auto_discover_domains()
domain = get_domain("bms_classrooms")

config = ScenarioConfig(
    project=ProjectConfig(namespace="captia", site_id="school1"),
    simulation=SimulationConfig(start="2026-01-01", end="2026-01-07", freq="5min", seed=42),
    domain=DomainReference(id="bms_classrooms"),
    sinks=[SinkConfig(type=SinkType.FILE, config={"path": "outputs/data.jsonl", "format": "jsonl"})],
)
sink = FileSinkAdapter(FileSinkConfig(path="outputs/data.jsonl", format="jsonl"))
runner = ScenarioRunner(config, domain, sink, validator=ContractValidator())
results = runner.run()
```

### MQTT Sink

```python
from synthetic_generator.sinks.mqtt import MQTTSinkAdapter, MQTTSinkConfig

sink = MQTTSinkAdapter(MQTTSinkConfig(
    broker_url="tcp://localhost:1883",
    topic_base="captia",
))
# Use with ScenarioRunner as above
```

### Docker Compose

```bash
docker compose -f compose/base.yaml -f compose/synthetic-multi.yaml --profile synthetic_all up -d
```

## Domains

| Domain | Assets | Variables | Description |
|--------|--------|-----------|-------------|
| `bms_classrooms` | 70 aulas | 21/aula | BMS: temperature, CO2, humidity, HVAC, energy |
| `industrial_refrigeration` | ~20 | 30+ | Cold storage: chambers, compressors, condensers |
| `discrete_manufacturing` | 8-13 | 22+ | Factory: machines, production, condition monitoring |

## Architecture

```
core/           Business logic (zero external deps)
  runner.py       ScenarioRunner (backfill + live)
  config.py       Pydantic v2 ScenarioConfig
  validator.py    ContractValidator (pre-emission)
  rate.py         RateController (token-bucket)
  clock.py        ClockPort + FakeClock
  anomalies.py    AnomalyEngine
ports/          Protocol interfaces
  domain.py       DomainAdapterPort
  sink.py         SinkAdapterPort
domains/        3 domain adapters + physics engines
sinks/          5 sink adapters (MQTT, File, Stdout, Composite, Null)
```

## Testing

```bash
uv run python -m pytest tests/ -v           # All 125 tests
uv run python -m pytest tests/ -m unit       # Unit only
uv run python -m pytest tests/ -m snapshot   # Determinism
uv run python -m pytest tests/ -m performance # Throughput
```

## Troubleshooting

**Import errors**: Run `uv pip install -e ".[dev]"` if `uv sync` doesn't install all deps.

**MQTT connection**: Ensure broker is running at `tcp://localhost:1883`. For Docker: `docker run -d -p 1883:1883 eclipse-mosquitto:2.0.18 mosquitto -c /dev/null -p 1883`

**Determinism issues**: Always use `np.random.default_rng(seed)` (not `np.random.seed()`). Check that FakeClock is used in tests.

## References

- [Specs](../../docs/specs/)
- [Module Docs](../../docs/02-modules/synthetic-generator.md)
- [Verification](../../docs/verification/)
