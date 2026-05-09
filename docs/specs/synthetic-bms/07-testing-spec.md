# 07 — Testing spec

## Context

Pirámide de tests siguiendo el patrón de `vendor/synthetic-generator/tests/`. Markers en `pyproject.toml` raíz coordinan ejecuciones.

## Pirámide

```
        /\
       /  \  e2e (smoke + slow)
      /----\
     /      \  integration (mqtt, influx, api)
    /--------\
   /          \  unit (services, models, parsers)
  /____________\
```

### Unit (markers: `unit`)

- **Ámbito**: lógica pura sin I/O.
- **Cobertura**: `bms_data_generator.config`, `bms_data_generator.services.runner_service`, `bms_data_generator.metrics`, `bms_calibration.faults`, `bms_calibration.school_calendar`, `bms_calibration.physics_overrides`.
- **Ejecución**: `task test:unit` → `uv run pytest -m unit -v`.

### Integration (markers: `integration`)

- **Ámbito**: API con FastAPI TestClient + mocks de MQTT/Influx.
- **Cobertura**: `bms_data_generator.api.{control,datasets,health}`.
- **Ejecución**: `task test:integration`.

### Smoke (markers: `smoke`)

- **Ámbito**: post-deploy con stack levantado.
- **Cobertura**: healthz, readyz, MQTT publish, Influx query, Grafana healthz.
- **Ejecución**: `task smoke` → scripts shell + `pytest -m smoke`.

### Snapshot (markers: `snapshot`)

- **Ámbito**: regresión determinista (sha256 sobre output).
- **Cobertura**: `bms_calibration.faults.FaultInjector`, dominios sintéticos.
- **Ejecución**: `task test:snapshot`.

### Performance (markers: `performance`, `slow`)

- **Ámbito**: throughput.
- **Cobertura**: 1 hora live mode → ≥ 700 pts/aula·h.
- **Ejecución**: `task test:performance`.

## Fixtures (compartidas en `conftest.py`)

```python
@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(seed=42)


@pytest.fixture
def short_time_index() -> pd.DatetimeIndex:
    return pd.date_range("2025-09-15 08:00", "2025-09-16 08:00", freq="5min")


@pytest.fixture
def mqtt_test_broker() -> str:
    """URL Mosquitto en docker-compose test."""
    return "tcp://localhost:1884"


@pytest.fixture
async def client():
    """FastAPI TestClient async."""
    from bms_data_generator.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def fault_config() -> dict:
    return {
        "sensor_drift": {"probability_per_day": 0.001, "drift_rate": 0.5},
        "valve_stuck": {"probability_per_day": 0.0005, "duration_minutes": 60},
        "fan_failure": {"probability_per_day": 0.0002, "duration_minutes": 240},
        "refrigerant_low": {"probability_per_day": 0.0001, "drift_rate": 2.0},
    }
```

## Validaciones obligatorias

| Validación | Test | Marcador |
|-----------|------|----------|
| Schema canónico CAPTIA en MQTT publish | `tests/integration/test_canonical_schema.py` | integration |
| `seed=42` produce hash idéntico | `extensions/bms_calibration/tests/test_determinism.py` | snapshot |
| 4 tipos de fallos cuando `faults_enabled=true` | `tests/integration/test_faults.py` | integration |
| Calendario lectivo correcto | `extensions/bms_calibration/tests/test_school_calendar.py` | unit |
| API auth requiere Bearer | `modules/bms-data-generator/tests/integration/test_api_control.py` | integration |
| Dump export genera line-protocol válido | `tests/e2e/test_dump_caseB.py` | smoke |
| Healthz responde 200 sin auth | `modules/bms-data-generator/tests/unit/test_api_health.py` | unit |
| Metrics endpoint formato Prometheus | `tests/integration/test_metrics_endpoint.py` | integration |

## Comandos

```bash
task test:unit          # rápido, sin docker
task test:integration   # requiere docker compose up
task test:smoke         # post-up
task test:snapshot      # determinismo
task test:performance   # slow
task test               # alias de unit
```

## Cobertura

- Mínimo: `bms_data_generator` ≥ 80% líneas.
- Reportar con `pytest --cov=modules/bms-data-generator/src --cov-report=term-missing`.

## Convenciones

- Sin `time.sleep(N)` en tests; usar `FakeClock` (vendor) o `asyncio.sleep` con timeouts.
- Tests deterministas con `seed=42`.
- Sin imports globales que impacten otros tests.
- Cleanup en fixtures (`yield` + teardown).

## Acceptance criteria

| ID | Criterio | Validación |
|----|----------|-----------|
| TS-01 | `task test:unit` PASS | Exit code 0 |
| TS-02 | `task test:integration` PASS con docker stack | Exit code 0 |
| TS-03 | Cobertura ≥ 80% para `bms_data_generator` | `pytest --cov` |
| TS-04 | Snapshot tests producen hash idéntico en 2 runs | `pytest -m snapshot` 2× |
| TS-05 | Sin `np.random.seed()` en código (solo `default_rng`) | `git grep -nE "np\\.random\\.seed\\(" -- ':!vendor'` vacío |
