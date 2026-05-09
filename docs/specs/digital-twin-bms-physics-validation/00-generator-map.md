# 00 — Mapa estructural del generador (Fase 0)

## Contexto

Mapa de ingredientes y flujos del generador BMS, derivado de inspección de código. Sirve como diagrama de referencia para `07-validator-design.md` (dónde insertar el validador) y `09-physical-observability.md` (qué señales surfacear).

## Vista hexagonal — vendor `synthetic-generator`

```mermaid
flowchart TB
  subgraph Core["core/ (agnóstico de dominio)"]
    Cfg[config.py<br/>ScenarioConfig]
    Run[runner.py<br/>ScenarioRunner]
    Anom[anomalies.py<br/>AnomalyEngine]
    Val[validator.py<br/>ContractValidator]
    Clk[clock.py<br/>SystemClock / FakeClock]
    Rate[rate.py<br/>token bucket]
    Mod[models.py<br/>DataPoint, Inventory]
  end

  subgraph Ports["ports/"]
    DPort[DomainAdapterPort<br/>Protocol]
    SPort[SinkAdapterPort<br/>Protocol]
  end

  subgraph Domains["domains/bms_classrooms/"]
    Plug[plugin.py<br/>BMSDomainPlugin]
    Inv[inventory.py<br/>build_inventory]
    Phy[physics/]
  end

  subgraph Sinks["sinks/"]
    Mqtt[mqtt.py<br/>MQTTSinkAdapter]
    File[file.py<br/>FileSinkAdapter]
    Std[stdout.py]
    Cmp[composite.py]
    Null[null.py]
  end

  Cfg --> Run
  Run --> Anom
  Run --> Val
  Run -.uses.-> Clk
  Run -.uses.-> Rate
  Run -->|simulate| Plug
  Plug -.implements.-> DPort
  Plug --> Inv
  Plug --> Phy
  Run -->|emit DataPoint| SPort
  Mqtt -.implements.-> SPort
  File -.implements.-> SPort
  Std -.implements.-> SPort
  Cmp -.implements.-> SPort
  Null -.implements.-> SPort
```

## Plug-in BMS — `domains/bms_classrooms/`

```mermaid
flowchart TB
  Plugin[plugin.py<br/>BMSDomainPlugin]
  Inv[inventory.py<br/>1..70 AULAxx + variables.yaml]
  Cal[calendar_generator.py<br/>school_mask, holidays]
  Sch[schedule_generator.py<br/>p_occupancy slots]
  Ctx[context.py<br/>build_context]

  subgraph Phy["physics/"]
    Env[environment.py<br/>outdoor_temperature<br/>daylight_lux]
    Occ[occupancy.py<br/>generate_occupancy_count]
    Act[actuators.py<br/>derive_scene<br/>thermostat_setpoint<br/>hvac_mode<br/>hvac_enable<br/>heating_valve_position<br/>light_state]
    Ind[indoor.py<br/>simulate_indoor_temperature<br/>simulate_co2<br/>simulate_humidity<br/>simulate_noise<br/>simulate_illuminance<br/>derive_pir_presence]
    En[energy.py<br/>simulate_power<br/>integrate_energy_kwh]
  end

  Plugin --> Inv
  Plugin --> Ctx
  Ctx --> Cal
  Ctx --> Sch
  Plugin --> Phy

  Env --> Ind
  Env --> Occ
  Sch --> Occ
  Cal --> Sch
  Occ --> Act
  Act --> Ind
  Ind --> En
  Occ --> En
  Act --> En
```

### Orden de cómputo por aula

1. `outdoor_temperature(index, cfg, rng)` y `daylight_lux(index)` → contexto exterior (compartido entre aulas).
2. `school_mask(index, calendar)` → bool por timestamp.
3. `p_occupancy(index, schedule, school_mask)` → probabilidad por timestamp.
4. `sample_aula_parameters(rng_aula)` → `(capacity, util)` por aula.
5. `generate_occupancy_count(...)` → serie `occupancy`.
6. `derive_scene(occupancy, school_mask, rng)` → `scene_mode`.
7. `thermostat_setpoint(scene, cfg, rng)` → `thermostat_setpoint`.
8. `hvac_mode(outdoor_temp, rng)` → `hvac_mode`.
9. `simulate_indoor_temperature(outdoor_temp, occupancy, setpoint, hvac_enable_prev, ...)` → `temperature` (nota: `hvac_enable` aquí debe venir del paso anterior; el código lo resuelve iterando — ver 01).
10. `hvac_enable(temperature, setpoint, occupancy, scene)` → `hvac_enable`.
11. `heating_valve_position(temperature, setpoint, mode)` → `heating_valve_pos`.
12. `simulate_co2(occupancy, hvac_enable, cfg, rng)` → `co2`.
13. `simulate_humidity(outdoor_temp, occupancy, cfg, rng)` → `humidity`.
14. `derive_pir_presence(occupancy, rng)` → `presence_pir`.
15. `light_state(occupancy, daylight_lux, rng)` → `light_state` (no aparece en variables.yaml como tal, alimenta `illuminance` y `power`).
16. `simulate_illuminance(daylight_lux, light_state, cfg, rng)` → `illuminance`.
17. `simulate_noise(occupancy, cfg, rng)` → `noise`.
18. `simulate_power(occupancy, light_state, hvac_enable, rng)` → `power`.
19. `integrate_energy_kwh(power)` → `energy`.

> **Acoplamientos a verificar** (ver `02-physics-questions.md`): el orden anterior implica que `temperature` se calcula con `hvac_enable` del paso previo. La realimentación HVAC ↔ T_indoor es **lazy** (1 paso de retraso).

## Capa BMS — `extensions/bms_calibration/`

```mermaid
flowchart LR
  Cal[school_calendar.py<br/>ValenciaSchoolCalendar<br/>4 períodos vacacionales]
  Po[physics_overrides.py<br/>3 hooks → None]
  Fi[faults.py<br/>FaultInjector<br/>4 tipos]
  Tests[tests/<br/>test_faults<br/>test_physics_overrides<br/>test_school_calendar<br/>test_determinism snapshot]

  Cal -.no usado en runtime.-> RT[runner_service]
  Po -.no invocado.-> RT
  Fi -.no cableado.-> RT
```

> **Estado**: estos 3 módulos son **inertes** en el path de generación actual. `runner_service._build_runner` no los importa. Solo los tests los ejercitan. Esta es una de las 3 deudas estructurales clave (ver `00-open-questions.md` L-PV-04, L-PV-05, L-PV-06).

## Capa servicio — `modules/bms-data-generator/`

```mermaid
flowchart TB
  subgraph FastAPI["FastAPI app (bms_data_generator)"]
    Main[main.py<br/>create_app]
    Hlth[api/health.py<br/>/healthz /readyz /metrics]
    Ctrl[api/control.py<br/>/v1/control/*]
    Data[api/datasets.py<br/>/v1/datasets/*]
    Cfg[config.py<br/>BMS_* env]
    Met[metrics.py<br/>captia_bms_*]
    Log[logging_config.py<br/>JSON]
  end

  subgraph Services["services/"]
    RS[runner_service.py<br/>RunnerService<br/>job state machine]
    DS[dump_service.py<br/>DumpService]
    CL[calibration_loader.py<br/>load_faults_config<br/>load_physics_overrides]
  end

  subgraph Vendor["vendor/synthetic-generator (lazy import)"]
    SR[ScenarioRunner]
    Plg[BMSDomainPlugin]
    Snk[Sinks]
  end

  Main --> Hlth
  Main --> Ctrl
  Main --> Data
  Ctrl --> RS
  Data --> DS
  RS -->|_build_runner| SR
  RS --> Plg
  RS --> Snk
  DS -->|_default_runner_factory| SR
  CL -.unused.-> RS
  CL -.unused.-> DS
```

## Pipeline de datos completo (Caso A — live)

```mermaid
sequenceDiagram
  autonumber
  participant API as FastAPI /v1/control/start
  participant RS as RunnerService
  participant SR as ScenarioRunner (vendor)
  participant Plg as BMSDomainPlugin
  participant Phy as physics/*
  participant Sink as MQTTSinkAdapter
  participant Mq as Mosquitto
  participant Tg as Telegraf
  participant Ix as InfluxDB
  participant Gf as Grafana

  API->>RS: start(config_path, mode=live, aulas=10)
  RS->>SR: _build_runner(config_path)
  RS->>SR: runner.run()
  SR->>Plg: build_inventory()
  SR->>Plg: build_context()
  loop por timestamp y aula
    SR->>Phy: simulate_*()
    Phy-->>SR: DataPoint(asset_id, variable, value, ts_ns)
    SR->>Sink: emit(point)
    Sink->>Mq: PUBLISH captia/{env}/{tenant}/{site}/{asset_id}/telemetry/{variable}
  end
  Mq->>Tg: SUBSCRIBE captia/+/+/+/+/telemetry/+
  Tg->>Tg: regex extract 5 tags
  Tg->>Ix: write captia_point
  Tg->>Ix: write captia_point_state (state_events bucket)
  Gf->>Ix: query Flux
  Gf-->>API: dashboards
```

## Sinks y schema canónico

```mermaid
flowchart LR
  subgraph DataPoint
    DP[asset_id<br/>variable<br/>value: float\|bool<br/>ts_ns: int<br/>quality: GOOD\|OUTLIER\|MISSING<br/>data_type<br/>point_type]
  end

  subgraph MQTT topic
    T[captia/{env}/{tenant}/{site}/{asset_id}/telemetry/{variable}]
  end

  subgraph Payload JSON
    P["value: float<br/>ts_ns: int"]
  end

  subgraph CAPTIA schema InfluxDB
    M[measurement: captia_point<br/>tags: captia_env, domain_id, site_id, asset_id, variable<br/>field: value]
  end

  DP -->|MQTTSink| T
  DP -->|MQTTSink| P
  T -->|Telegraf| M
  P -->|Telegraf| M
```

## Buckets InfluxDB (existentes — no se modifican)

| Bucket | Retención | Origen | Uso ML |
|--------|-----------|--------|--------|
| `telemetry` | 14 d | raw 5 s ingestion | alertas tiempo real |
| `telemetry_1m` | 30 d | downsample (mean/min/max) | corto plazo |
| `telemetry_15m` | 90 d | rollup | medio plazo |
| `telemetry_1h` | 365 d | rollup | **principal ML** |
| `state_events` | 90 d | on-change (boolean, setpoint, fault) | clasificación de eventos |
| `captia_metadata` | ∞ | catálogo (unit, range, metric_kind) | referencia |

> **Propuesta para validación física** (`09-physical-observability.md`): nuevo bucket `physics_metrics` (90 d) con measurement `captia_physics_point` (mismos 5 tags + `value`) para no contaminar `telemetry`.

## Componentes inertes / pendientes de cableado

| Componente | Ubicación | Estado | Bloquea |
|------------|-----------|--------|---------|
| `bms_calibration.faults.FaultInjector` | `extensions/bms_calibration/.../faults.py` | Definido, **no invocado** desde `runner_service` | Caso C real (faults visibles en `state_events`) |
| `bms_calibration.physics_overrides.get_overrides` | idem | Hooks → `None`, no invocados | L-01 calibración real |
| `bms_calibration.school_calendar.ValenciaSchoolCalendar` | idem | Definido, **no invocado** | Calendario unificado y oficial |
| `services.calibration_loader.{load_faults_config, load_physics_overrides}` | `modules/.../services/calibration_loader.py` | Definidos pero sin caller en runner/dump | Wiring de avería + override |
| `core.validator.ContractValidator` | `vendor/.../core/validator.py` | Definido, **no instanciado** en BMS path | Validación contractual pre-emisión |
| `core.config.PerturbationsConfig` (jitter_ms, duplicate_probability, out_of_order_probability, gap_probability) | `vendor/.../core/config.py` | Campos definidos, **no aplicados** en runner | Test de robustez ingest |
| `core.control_utils.{HysteresisController, MinOnOffTimer, PIController, LeadLagController}` | `vendor/.../core/control_utils.py` | Disponibles, **no usados** por physics BMS | Realismo HVAC (anti short-cycle, PI control) |

## Implicaciones para validación física

El mapa muestra que:

1. **Hay seams claras** para insertar un validador físico sin tocar `vendor/`:
   - Wrapper de sink (entre `ScenarioRunner` y los `MQTTSink`/`FileSink`).
   - Post-run analyzer en `RunnerService` y `DumpService` (después de `runner.run()`).
   - Domain adapter wrapper (entre `BMSDomainPlugin` y `core/runner`) — más invasivo.
2. **El cableado de averías y calibración está pre-fabricado** pero ocioso: la validación física puede empezar consumiendo `FaultEvent` desde el inyector si se le añade un caller.
3. **El catálogo de variables real** (`variables.yaml`) y el aspiracional (`02-domain-spec.md`) divergen → la spec de validación se ancla al **catálogo real** del vendor; la divergencia se documenta.
