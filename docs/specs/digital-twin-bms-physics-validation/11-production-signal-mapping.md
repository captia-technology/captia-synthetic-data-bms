# 11 — Mapeo de señales canónicas vendor ↔ producción

## Contexto

Tras revisar `docs/influxdb-simarro-buckets.pptx` (snapshot ground truth simarro-prod 2026-03-28) y `docs/captia-connect-partner-integration.pptx` (contrato canónico CAPTIA-CONNECT v1.0 2026-05), confirmamos que **el catálogo de variables que produce el vendor `synthetic-generator` no coincide con el catálogo real de producción en `simarro-prod`**.

Esto eleva L-PV-01 a **BLOCKER** crítico para que el generador sintético sea **drop-in replacement** de telemetría real durante desarrollo de modelos ML, dashboards, alertas y entrenamiento.

**Decisión**: este documento define el **mapeo canónico vendor → producción** y propone implementación vía override de `config/domains/bms_classrooms/variables.yaml` (path local prevalece sobre vendor por inventory loader) sin modificar `vendor/`.

## Fuentes de verdad

| Fuente | Tipo | Fecha | Cita |
|--------|------|-------|------|
| `docs/influxdb-simarro-buckets.pptx` slide 14 | Snapshot ground truth simarro-prod | 2026-03-28 | "Variables reales en AULA01 (gateway BMS · ~30)" |
| `docs/influxdb-simarro-buckets.pptx` slide 14 | Snapshot Sensup sensor 0004742C0169 | 2026-03-28 | "Variables en sensor 0004742C0169 (Sensup · 9 continuas)" |
| `docs/captia-connect-partner-integration.pptx` slide 5 | Contrato 7-segment topic | 2026-05 | "captia/{env}/{tenant}/{site}/{device}/{stream}/{name}" |
| `docs/captia-connect-partner-integration.pptx` slide 6 | Contrato payload JSON | 2026-05 | `{"value": float, "ts_ns": int}` |
| `docs/captia-connect-partner-integration.pptx` slide 7 | Routing on-change suffix glob | 2026-05 | sufijos `*_cmd`, `*_ack`, `*_state`, etc. |
| `docs/captia-connect-partner-integration.pptx` slide 8 | metric_kind enum | 2026-05 | analog_gauge / bool_presence / counter / bool_state / setpoint_step / skip |
| `vendor/synthetic-generator/config/domains/bms_classrooms/variables.yaml` | Vendor catalog | 2026-05-09 | 21 variables generadas |

## Catálogo real producción (`simarro-prod` ground truth)

### Gateway BMS (asset_id = `AULA01`, ~30 variables)

| Variable producción | Naming | metric_kind inferido | Routing | Observaciones |
|--------------------|--------|---------------------|---------|---------------|
| `temperature_01` | snake `_NN` | analog_gauge | continuous | termo principal; sufijo `_01` indica canal/sensor |
| `temperature_01_sp` | snake `_sp` | setpoint_step | on_change (`*_sp`) | setpoint asociado al canal `_01` |
| `temperature-indoor` | kebab | analog_gauge | continuous | termo ambiente (puede ser sensor distinto) |
| `relative-humidity` | kebab | analog_gauge | continuous | RH |
| `co2` | plain | analog_gauge | continuous | CO₂ ppm |
| `t-voc` | kebab | analog_gauge | continuous | TVOC ppb |
| `iaq-index` | kebab | analog_gauge | continuous | IAQ índice 0-500 |
| `avg-sound-level` | kebab | analog_gauge | continuous | dB(A) media |
| `max-sound-level` | kebab | analog_gauge | continuous | dB(A) pico |
| `luminosity` | plain | analog_gauge | continuous | lux |
| `occupancy` | plain | bool_presence | continuous | presencia bool |
| `people-count` | kebab | analog_gauge | continuous | conteo persons |
| `power_01` | snake `_NN` | counter o analog_gauge | continuous | potencia consumida (canal `_01`) |
| `ac_state` | snake `_state` | bool_state | on_change (`*_state`) | estado del aire acondicionado |
| `ac_control` | snake | setpoint_step o bool_state | on_change (regla custom) | comando del AC |
| `aire` | plain | bool_state | continuous | sensor aire (sin sufijo, ¿continuous?) |
| `aire_state` | snake `_state` | bool_state | on_change | estado del relé aire |
| `fan_speed_01` | snake `_NN` | analog_gauge | continuous | velocidad ventilador 1 |
| `fan_speed_01_state` | snake `_state` | bool_state | on_change | estado on/off ventilador 1 |
| `fan_speed_02` + `_state` | idem | idem | idem | ventilador 2 |
| `fan_speed_03` + `_state` | idem | idem | idem | ventilador 3 |
| `light_01` | snake `_NN` | bool_state o analog_gauge | continuous (?) | luz 1 |
| `light_01_state` | snake `_state` | bool_state | on_change | relé luz 1 |
| `light_02` + `_state` | idem | idem | idem | luz 2 |
| `valve_control` | snake | setpoint_step | on_change | comando válvula |
| `valve_state` | snake `_state` | bool_state | on_change | feedback válvula |

### Sensor Sensup (asset_id = `0004742C0169`, 9 variables continuas)

| Variable producción | Mismo dominio que BMS gateway |
|--------------------|------|
| `avg-sound-level` | ✓ |
| `iaq-index` | ✓ |
| `luminosity` | ✓ |
| `max-sound-level` | ✓ |
| `occupancy` | ✓ |
| `people-count` | ✓ |
| `relative-humidity` | ✓ |
| `temperature-indoor` | ✓ |
| `t-voc` | ✓ |

> Importante: el Sensup no expone HVAC, válvulas, fans, ni luces. Es sensor IAQ puro. Si `n_aulas` mezcla gateways y Sensups, el catálogo emitido debe variar por asset.

## Catálogo vendor actual (`variables.yaml`)

| Variable vendor | Tipo | Categoría |
|-----------------|------|-----------|
| `temperature` | float, °C, sensor | ENVIRONMENTAL |
| `humidity` | float, %RH, sensor | ENVIRONMENTAL |
| `co2` | float, ppm, sensor | ENVIRONMENTAL |
| `iaq_index` | float, calculated | ENVIRONMENTAL |
| `noise` | float, dB(A) | ENVIRONMENTAL |
| `illuminance` | float, lux | ENVIRONMENTAL |
| `occupancy` | integer, persons | OCCUPANCY |
| `presence_pir` | boolean | OCCUPANCY |
| `outdoor_temp` | float, °C, sensor | EXTERNAL |
| `daylight_lux` | float, lux | EXTERNAL |
| `thermostat_setpoint` | float, °C, setpoint | HVAC |
| `hvac_mode` | enum | HVAC |
| `hvac_enable` | boolean, actuator | HVAC |
| `heating_valve_pos` | float, % | HVAC |
| `scene_mode` | enum | CONTROL |
| `relay_1..relay_4` | boolean | CONTROL |
| `power` | float, W | ENERGY |
| `energy` | float, kWh, counter | ENERGY |

## Mapeo canónico vendor → producción

Tabla de equivalencias propuesta. **Convenciones**:
- ✅ Mapeo trivial (renombrar).
- 🔧 Necesita transform o duplicar.
- ➕ Variable producción que vendor no genera (gap).
- ➖ Variable vendor que no existe en producción (extra; emitir o no según política).

| Vendor (actual) | Producción (canónica) | Ruta | Notas |
|-----------------|----------------------|------|-------|
| `temperature` | `temperature_01` | ✅ | Renombrar; el vendor solo tiene 1 canal de temperatura por aula → mapea a `_01`. |
| `temperature` (mismo) | `temperature-indoor` | 🔧 | Producción tiene **2 termos** (`_01` y `-indoor`). El vendor podría emitir el **mismo valor** a ambos nombres, o solo uno (recomendado: solo `_01`). |
| `thermostat_setpoint` | `temperature_01_sp` | ✅ | Renombrar al sufijo `_sp` y prefijo del canal. |
| `humidity` | `relative-humidity` | ✅ | Renombrar (kebab). |
| `co2` | `co2` | ✅ | Igual. |
| `iaq_index` | `iaq-index` | ✅ | Renombrar (kebab). |
| `noise` | `avg-sound-level` | ✅ | Renombrar; producción distingue `avg-` vs `max-sound-level`. Vendor solo modela 1. |
| (no existe) | `max-sound-level` | ➕ | Generar como `avg-sound-level + N(0, ~5)` clipped a 110 dB(A) (estimado). Modelo separado en physics o aliasing. |
| `illuminance` | `luminosity` | ✅ | Renombrar. |
| `occupancy` (integer) | `people-count` | ✅ | Renombrar; producción tiene int separado. |
| (no existe directamente) | `occupancy` (bool) | 🔧 | Producción tiene `occupancy` como **bool_presence**. Mapear `presence_pir → occupancy`. |
| `presence_pir` | `occupancy` (bool) | 🔧 | Renombrar a `occupancy` para alinear con producción (bool_presence). |
| (no existe en vendor) | `t-voc` | ➕ | Generar como ~CO₂ correlado, en ppb. Modelo nuevo o derivar de `(co2 - 400) * factor`. |
| `power` | `power_01` | ✅ | Renombrar (sufijo canal). |
| `energy` | (no existe en producción slide 14) | ➖ | El snapshot no la lista. Mantener como derivada interna o emitir solo si necesaria para Caso B. |
| `outdoor_temp` | (no existe en AULA01 — es del sitio) | 🔧 | En producción la T_outdoor es de un asset distinto (e.g., `OUTDOOR` o `WEATHER`). Nuestro vendor la asigna por aula; mejor emitir como `asset_id=OUTDOOR variable=temperature-outdoor` (kebab). |
| `daylight_lux` | (no existe en producción) | ➖ | Variable interna del modelo (alimenta `illuminance` y `power`). No emitir. |
| `hvac_mode` | `ac_control` | 🔧 | Producción usa `ac_control` (setpoint_step on_change). El enum vendor {off, heat, cool, auto} se mapea: emitir como string o codificar a int. |
| `hvac_enable` | `ac_state` | ✅ | Renombrar; ambos son bool. |
| `heating_valve_pos` | `valve_control` | ✅ | Renombrar; producción separa `valve_control` (comando) y `valve_state` (feedback). El vendor modela un solo continuo. |
| (derivado) | `valve_state` | ➕ | Generar como `1 if valve_control > 0 else 0` (proxy bool feedback). |
| `scene_mode` | (no existe en producción slide 14) | ➖ | Variable interna; no emitir. |
| `relay_1..relay_4` | `light_01_state`, `light_02_state`, `fan_speed_01_state`, `fan_speed_02_state`, ... | 🔧 | Producción usa nombres específicos. Mapear: relay_1→light_01_state, relay_2→light_02_state, relay_3→fan_speed_01_state, relay_4→fan_speed_02_state. **Pero** vendor no alimenta los relays con lógica física hoy (siempre 0). Necesita modelo. |
| (no existe) | `light_01`, `light_02` (continuos) | ➕ | Producción tiene continuos además de `_state`. Probable lectura de luminosidad por canal. Generar como `daylight_lux * factor + indoor_artificial * light_state`. |
| (no existe) | `fan_speed_01..03` (continuos) | ➕ | Velocidad ventilador 0-100 o 0-3. Sin modelo en vendor. |
| (no existe) | `aire`, `aire_state` | ➕ | Sensor "aire" + relé. Sin modelo. Podría ser un proxy de calidad de aire compuesto o un sensor genérico. Documentar como TODO. |

## Catálogo derivado (canónico para sintético, alineado con producción)

Esta es la **propuesta de `config/domains/bms_classrooms/variables.yaml`** override que reemplaza el del vendor:

```yaml
# config/domains/bms_classrooms/variables.yaml — override producción-aligned
# Source of truth: docs/influxdb-simarro-buckets.pptx slide 14, captia-connect-partner-integration.pptx slide 8.

asset_types:
  classroom:
    variables:
      # ── Sensors: Environmental (continuous) ──────────────────────
      - name: temperature_01            # vendor: temperature
        data_type: float
        unit: "°C"
        point_type: sensor
        metric_kind: analog_gauge
        category: ENVIRONMENTAL
        range: [10.0, 35.0]
        producer_function: simulate_indoor_temperature

      - name: temperature-indoor        # opcional: misma fuente, distinto nombre (alias)
        data_type: float
        unit: "°C"
        point_type: sensor
        metric_kind: analog_gauge
        category: ENVIRONMENTAL
        range: [10.0, 35.0]
        producer_function: simulate_indoor_temperature  # mismo valor

      - name: relative-humidity         # vendor: humidity
        data_type: float
        unit: "%RH"
        point_type: sensor
        metric_kind: analog_gauge
        category: ENVIRONMENTAL
        range: [10.0, 90.0]
        producer_function: simulate_humidity

      - name: co2                       # idem
        data_type: float
        unit: ppm
        point_type: sensor
        metric_kind: analog_gauge
        category: ENVIRONMENTAL
        range: [400.0, 2200.0]
        producer_function: simulate_co2

      - name: t-voc                     # NUEVO — derivar de co2
        data_type: float
        unit: ppb
        point_type: sensor
        metric_kind: analog_gauge
        category: ENVIRONMENTAL
        range: [0.0, 3000.0]
        producer_function: derive_tvoc_from_co2

      - name: iaq-index                 # vendor: iaq_index
        data_type: float
        unit: index
        point_type: calculated
        metric_kind: analog_gauge
        category: ENVIRONMENTAL
        range: [0.0, 500.0]
        producer_function: derive_iaq_index

      - name: avg-sound-level           # vendor: noise
        data_type: float
        unit: "dB(A)"
        point_type: sensor
        metric_kind: analog_gauge
        category: ENVIRONMENTAL
        range: [25.0, 90.0]
        producer_function: simulate_noise

      - name: max-sound-level           # NUEVO — derivar de avg + ruido extra
        data_type: float
        unit: "dB(A)"
        point_type: sensor
        metric_kind: analog_gauge
        category: ENVIRONMENTAL
        range: [25.0, 110.0]
        producer_function: derive_max_sound_from_avg

      - name: luminosity                # vendor: illuminance
        data_type: float
        unit: lux
        point_type: sensor
        metric_kind: analog_gauge
        category: ENVIRONMENTAL
        range: [0.0, 2500.0]
        producer_function: simulate_illuminance

      # ── Sensors: Occupancy ──────────────────────────────────────
      - name: people-count              # vendor: occupancy (integer)
        data_type: integer
        unit: persons
        point_type: sensor
        metric_kind: analog_gauge
        category: OCCUPANCY
        range: [0.0, 100.0]
        producer_function: generate_occupancy_count

      - name: occupancy                 # vendor: presence_pir
        data_type: boolean
        unit: bool
        point_type: sensor
        metric_kind: bool_presence
        category: OCCUPANCY
        producer_function: derive_pir_presence  # alias semántico — bool

      # ── Actuators: HVAC (on_change) ─────────────────────────────
      - name: temperature_01_sp         # vendor: thermostat_setpoint
        data_type: float
        unit: "°C"
        point_type: setpoint
        metric_kind: setpoint_step
        storage_mode: on_change
        category: HVAC
        range: [14.0, 30.0]
        producer_function: thermostat_setpoint

      - name: ac_control                # vendor: hvac_mode
        data_type: string
        unit: enum
        point_type: actuator
        metric_kind: setpoint_step
        storage_mode: on_change
        category: HVAC
        enum_values: [off, heat, cool, auto]
        producer_function: hvac_mode

      - name: ac_state                  # vendor: hvac_enable
        data_type: boolean
        unit: bool
        point_type: actuator
        metric_kind: bool_state
        storage_mode: on_change
        category: HVAC
        producer_function: hvac_enable

      - name: valve_control             # vendor: heating_valve_pos
        data_type: float
        unit: "%"
        point_type: actuator
        metric_kind: analog_gauge
        category: HVAC
        range: [0.0, 100.0]
        producer_function: heating_valve_position

      - name: valve_state               # NUEVO — derivar de valve_control
        data_type: boolean
        unit: bool
        point_type: actuator
        metric_kind: bool_state
        storage_mode: on_change
        category: HVAC
        producer_function: derive_valve_state_from_position

      # ── Actuators: Fans (on_change states + continuous speeds) ──
      - name: fan_speed_01
        data_type: float
        unit: "%"
        point_type: sensor
        metric_kind: analog_gauge
        category: HVAC
        range: [0.0, 100.0]
        producer_function: derive_fan_speed_from_hvac

      - name: fan_speed_01_state
        data_type: boolean
        unit: bool
        point_type: actuator
        metric_kind: bool_state
        storage_mode: on_change
        category: HVAC
        producer_function: derive_fan_state_from_hvac

      - name: fan_speed_02
        data_type: float
        unit: "%"
        ... (idem para 02 y 03)

      # ── Actuators: Lights (on_change states + continuous values) ──
      - name: light_01
        data_type: float
        unit: lux
        point_type: sensor
        metric_kind: analog_gauge
        category: CONTROL
        range: [0.0, 600.0]
        producer_function: derive_light_value_from_state

      - name: light_01_state            # vendor: relay_1
        data_type: boolean
        unit: bool
        point_type: actuator
        metric_kind: bool_state
        storage_mode: on_change
        category: CONTROL
        producer_function: light_state

      - name: light_02 + light_02_state ... idem

      # ── Generic "aire" (TBD) ────────────────────────────────────
      - name: aire                      # NUEVO — placeholder o índice compuesto
        data_type: float
        ...
        TBD: requires clarification with CAPTIA Tech.

      - name: aire_state
        data_type: boolean
        ...

      # ── Sensors: Energy ─────────────────────────────────────────
      - name: power_01                  # vendor: power
        data_type: float
        unit: W
        point_type: sensor
        metric_kind: analog_gauge       # producción no usa counter aquí (slide 14)
        category: ENERGY
        range: [0.0, 6000.0]
        producer_function: simulate_power
```

**Variables ELIMINADAS del vendor** (ya no emitir):
- `presence_pir` → renombrada a `occupancy` (bool_presence).
- `humidity` → renombrada a `relative-humidity`.
- `noise` → renombrada a `avg-sound-level`.
- `illuminance` → renombrada a `luminosity`.
- `iaq_index` → renombrada a `iaq-index` (kebab).
- `temperature` → renombrada a `temperature_01`.
- `power` → renombrada a `power_01`.
- `thermostat_setpoint` → renombrada a `temperature_01_sp`.
- `hvac_mode` → renombrada a `ac_control`.
- `hvac_enable` → renombrada a `ac_state`.
- `heating_valve_pos` → renombrada a `valve_control`.
- `relay_1..relay_4` → renombrados / desaparecen (sustituidos por nombres específicos).
- `scene_mode` → variable interna, no emitir.
- `outdoor_temp` → mover a asset_id=OUTDOOR como `temperature-outdoor`.
- `daylight_lux` → variable interna, no emitir.
- `energy` → eliminada (no presente en producción slide 14) o emitir solo si requerido por Caso B.

## Mapeo de assets

Producción tiene **2 tipos de asset_id** en simarro-prod:

| asset_id | Tipo | Variables emitidas |
|----------|------|-------------------|
| `AULA01..AULAnn` | Gateway BMS | ~30 variables (lista arriba completa) |
| `0004742C0169..` (hex 12 chars) | Sensor Sensup | 9 variables continuas (subset IAQ) |
| `OUTDOOR` o `WEATHER` (propuesto) | Estación meteo | `temperature-outdoor`, `solar_irradiance`, `daylight-lux` |

Para sintético propongo:
- `AULA01..AULA10` (default) emiten catálogo gateway BMS completo.
- Opcional: añadir 1-2 sensores Sensup adicionales por aula (subset IAQ) con asset_id sintético `SENSUP01..` para que el dataset incluya 2 fuentes de IAQ por aula (típico en producción).
- `OUTDOOR` emite las variables de contexto exterior compartidas.

## Bucket `telemetry_events` (faltante)

`docs/influxdb-simarro-buckets.pptx` slide 8 documenta el **7º bucket**:

```yaml
bucket: telemetry_events
retention: 90d
measurement: captia_cmd_event
tags: captia_env, domain_id, site_id, asset_id, variable + event_type
event_type ∈ {cmd_authorized, cmd_rejected, sniper_error}
fields: cmd_id, metric, target, reason, error, source, detail (string)
producer: Telegraf output #3 (2º mqtt_consumer)
topics: captia/+/+/+/+/event/+, captia/sniper/event
consumer: Events Engine, dashboards de auditoría
```

**Estado actual del repo**: NO existe.
- `infra/influxdb/init/init_buckets_tasks.sh:62-67` solo crea 6 buckets.
- `infra/telegraf/telegraf.conf:35-50` solo tiene 1 `mqtt_consumer` (telemetry).

**Acción** (T-PV-NEW): añadir bucket + segundo `mqtt_consumer` en Telegraf con `topics = ["captia/+/+/+/+/event/+"]`. Ver `10-implementation-readiness.md`.

## Measurement de `state_events` divergente

`docs/influxdb-simarro-buckets.pptx` slide 8 dice **explícitamente**:

> Measurement: `captia_point` (NO captia_point_state)

Pero `infra/telegraf/telegraf.conf:101` hace:

```toml
[[processors.clone]]
  namepass = ["captia_point"]
  name_override = "captia_point_state"   # ← divergente
```

**Implicación**: en producción, `state_events` y `telemetry` usan el **mismo measurement** (`captia_point`); solo difieren en bucket. Las queries Flux son más simples (un solo `from(bucket).filter(_measurement=="captia_point")` cubre ambos).

En nuestro stack local, la query debería filtrar por measurement distinto si quiere acceder a `state_events` — incompatibilidad de ergonomía.

**Acción** (T-PV-NEW): cambiar `name_override = "captia_point_state"` → eliminar línea, dejar measurement `captia_point` también para state_events. Tests asociados se actualizan.

## Topic 7-segment (clarificación)

`docs/captia-connect-partner-integration.pptx` slide 5 confirma:

```
captia / {env} / {tenant=domain_id} / {site} / {device=asset_id} / {stream} / {name=variable}
   0       1            2                3              4               5            6
```

**Stream values canónicos** (5 enum):
- `telemetry` — sensor readings / device state
- `cmd` — comandos del adapter
- `ack` — ack del device
- `state` — device state updates (¿?¿este se usa? overlap con bucket state_events. Aclarar)
- `event` — platform events (cmd_authorized, errors)

**Estado actual sintético**: solo emitimos `telemetry`. **No emitimos** `cmd`, `ack`, `state`, `event`. Caso C (faults) podría emitir `event` con el `FaultEvent`.

## Convención on-change suffix glob

`docs/captia-connect-partner-integration.pptx` slide 7 enumera los sufijos auto-routed a state_events:

```
*_cmd  *_ack  *_status  *_state  *_st  *_active
*_enable  *_in_progress  relay_*  *_setpoint  *_sp  *_mode
```

Nuestro `infra/telegraf/telegraf.conf:103-117` está alineado **excepto** que añadimos `fault.*` (no en producción).

Variables del catálogo aligned-producción que matchean este glob:
- `temperature_01_sp` → `*_sp` ✓ on_change ✓
- `ac_control` → ❌ (no termina en sufijo on_change). Pero PPTX dice setpoint_step → on_change. Discrepancia. Probablemente Telegraf en producción tiene tagpass específico para `ac_control`.
- `ac_state` → `*_state` ✓
- `*_state` general (valve_state, fan_speed_*_state, light_*_state) → ✓
- `valve_control` → ❌ (no termina en sufijo glob). Setpoint? Igual que ac_control.

**Hallazgo nuevo L-PV-NN**: la convención de naming + glob no cubre todos los actuadores que en realidad son on_change (ej. `ac_control`, `valve_control`). Probable que Telegraf de producción tenga tagpass extendido o un `metric_kind`-driven routing distinto.

## Routing on-change y discrepancia con `metric_kind`

PPTX `partner` slide 8 dice:

| metric_kind | Storage | Stats |
|-------------|---------|-------|
| analog_gauge | continuous | mean/min/max |
| bool_presence | continuous | duty/count_rise/last |
| bool_state | on_change | last/count_rise |
| setpoint_step | on_change | last |
| counter | continuous | sum (delta) |

Implica que el routing on-change debe basarse en `metric_kind` (bool_state o setpoint_step) **o** en el suffix glob. Probablemente producción combina ambos.

Variables como `ac_control` (setpoint_step según partner spec) van a state_events vía catálogo `captia_metadata`, no por glob de Telegraf.

**Implicación para nuestro stack**: necesitaríamos publicar `captia_point_meta` con cada variable + `metric_kind` + `storage_mode` para que Telegraf (o el sink directamente) decida correctamente. Hoy nos basamos solo en glob → cubre la mayoría pero no todos.

## Tabla resumen — divergencias críticas vendor ↔ producción

| Aspecto | Vendor (actual) | Producción (PPTX) | Severity |
|---------|-----------------|------------------|----------|
| Variables nombradas | snake plain (`temperature`, `power`, `humidity`...) | mix snake+kebab+sufijo `_NN`/`_state`/`_sp` (`temperature_01`, `relative-humidity`, `power_01`, `valve_state`...) | **BLOCKER** |
| Buckets InfluxDB | 6 (telemetry, _1m, _15m, _1h, state_events, captia_metadata) | **9** (los 6 + telemetry_events + _monitoring + _tasks) | High (falta telemetry_events) |
| measurement state_events | `captia_point_state` (override Telegraf) | `captia_point` (igual que telemetry) | Medium (ergonomía queries) |
| catálogo `captia_metadata` | bucket creado pero **vacío** (no metadata-bootstrap) | poblado con `captia_point_meta` (21 fields), `captia_domain_meta`, `captia_device_registry` | Medium |
| stream Telegraf consumer | solo `telemetry` (1 mqtt_consumer) | `telemetry` + `event` (2 mqtt_consumer + 3 outputs) | High (falta event) |
| Routing on-change | suffix glob (`*_state`, `*_sp`, etc.) + `fault.*` extra | suffix glob + `metric_kind`-driven (`bool_state`, `setpoint_step`) | Medium |
| asset_id naming | uppercase `AULA01..AULA10` | `AULA01..AULAnn` (gateway) + `0004742C0169` (hex 12 char Sensup) + `global`, `AULA_AUDIT`, `AULA_TEST` (otros) | Low (cosmético) |
| `OUTDOOR` asset | no existe (outdoor_temp se asigna a cada aula) | implícito (probablemente otro asset_id) | Medium |
| Eliminados producción | (no aplicable) | `topic`, `host`, `point_type` (commit c1997bb 2026-04-13) | Low (no tenemos `point_type` como tag) |

## Implicaciones para la spec set

Reglas afectadas en `04-physical-plausibility-rules.md`:

| Regla | Cambio requerido |
|-------|------------------|
| R-INF-01 | Añadir verificación de mapping vendor↔producción (variable names match catálogo). |
| R-INF-03 | Catálogo coverage debe ser contra **variables.yaml producción-aligned**, no contra el del vendor. |
| Todas las R-* que mencionan `temperature` | Renombrar referencias internamente a `temperature_01` (o usar producer_function). |
| Todas las R-* que mencionan `humidity` | → `relative-humidity`. |
| Todas las R-* que mencionan `power` | → `power_01`. |
| Todas las R-* que mencionan `noise` | → `avg-sound-level`. |
| Todas las R-* que mencionan `illuminance` | → `luminosity`. |
| Todas las R-* que mencionan `iaq_index` | → `iaq-index`. |
| Todas las R-* que mencionan `presence_pir` | → `occupancy` (bool). |
| Todas las R-* que mencionan `occupancy` (int) | → `people-count`. |
| Todas las R-* que mencionan `thermostat_setpoint` | → `temperature_01_sp`. |
| Todas las R-* que mencionan `hvac_mode` | → `ac_control`. |
| Todas las R-* que mencionan `hvac_enable` | → `ac_state`. |
| Todas las R-* que mencionan `heating_valve_pos` | → `valve_control` + verificación cross con `valve_state`. |
| Todas las R-* que mencionan `relay_*` | → mapping específico (`light_01_state`, etc.). |

**Decisión**: las reglas YA escritas en `04-*` se mantienen con nombres vendor para no destruir trazabilidad code→spec del modelo físico (cada regla cita `physics/*.py` que usa los nombres vendor). El **producer_function** de la nueva `variables.yaml` mantiene el binding entre regla y physics. La traducción a producción ocurre en la capa de output (sink wrapper o adaptador).

Ver `10-implementation-readiness.md` actualizado para tareas T-PV-NN nuevas.

## Implementación propuesta — opciones

### Opción 1 (recomendada) — Override variables.yaml local

- Crear `config/domains/bms_classrooms/variables.yaml` con catálogo producción-aligned.
- El plug-in vendor `BMSDomainPlugin` busca en `config/domains/.../variables.yaml` antes de su propio (verificar en `inventory.py:105-126` el orden de resolución).
- Añadir aliasing en el plug-in para que `producer_function` original (e.g., `simulate_indoor_temperature`) emita con nuevo `name`.

**Pros**: no toca vendor; reversible; compatible con nuevos releases del vendor.
**Cons**: requiere que el plug-in soporte aliasing (puede necesitar PATCH menor del vendor).

### Opción 2 — Aliasing layer en sink wrapper

- Crear `extensions/bms_signal_alias/src/bms_signal_alias/alias_sink.py`.
- Wrapper SinkAdapter que reescribe `point.variable` antes de delegar.
- Mapping table en YAML: `vendor_name → production_name`.

**Pros**: completamente sin tocar vendor; rotación trivial.
**Cons**: el inventario sigue diciendo nombres vendor, lo que podría confundir downstream.

### Opción 3 — PATCH del vendor (`vendor/synthetic-generator/PATCHES/`)

- Modificar `variables.yaml` y `physics/*.py` directamente con nombres producción.
- Aplicar como patch versionado.

**Pros**: fuente única.
**Cons**: rompe Regla 003 (vendoring read-only); cada update vendor reaplica patch.

**Recomendación**: **Opción 1** + **Opción 2 combinadas**:
1. Override de `variables.yaml` local (Opción 1) para que el inventario refleje producción.
2. Mientras el plug-in vendor no soporte aliasing, añadir `AliasSink` (Opción 2) entre runner y MQTT/File sinks.
3. Cuando vendor v2 soporte aliasing nativo (futuro), retirar AliasSink.

Ver `10-implementation-readiness.md` para los tasks T-PV-21..23.

## Validación de la implementación

Al completar el mapeo, verificar:

1. `make smoke-schema` (script `verify_canonical_schema.sh`) confirma que las variables emitidas a InfluxDB coinciden con catálogo producción.
2. `tests/integration/test_canonical_schema.py` se actualiza con asserts contra catálogo nuevo.
3. Dashboard `bms_overview.json` se renombra paneles para usar nombres producción (`temperature_01` en lugar de `temperature`, etc.).
4. Documentar en `STATUS.md` la conformancia con producción.

## Cómo subir confidence del score (`08-physical-realism-score.md`)

Tras implementar el mapeo:
- D10 (Compatibilidad CAPTIA) sube de 0.80 a **1.00** porque el catálogo emitido coincide con producción.
- R-INF-03 (catalog coverage) PASA con confianza alta.
- Score interno global proyectado: **~0.96** (de 0.94 actual).

Si además se cablea `telemetry_events` y `cmd`/`ack`/`event` streams: cobertura de pipeline producción completa.
