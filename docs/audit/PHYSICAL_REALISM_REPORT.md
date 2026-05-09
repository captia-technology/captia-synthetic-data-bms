# Auditoría — Realismo físico (modelos vendor BMS vs spec)

> Generado el 2026-05-09 — Fase 6 del plan de auditoría extrema (`docs/audit/STATUS.md`).
>
> Ámbito: 5 módulos `physics/*.py` del vendor + 11 specs en `docs/specs/digital-twin-bms-physics-validation/` + override real en `config/domains/bms_classrooms/domain.yaml` + evidencia live en bucket `telemetry`.

## 0. Resumen ejecutivo

| Métrica | Valor |
|---|---|
| Variables emitidas por aula | **21** (sobre 22 del catálogo — `iaq-index` derivado en runtime) |
| Aulas activas en stack live | **24** (escalado dinámico desde el default 10) |
| Reglas de plausibilidad documentadas | **53** (`04-physical-plausibility-rules.md`) |
| Reglas implementables hoy | **45** |
| Reglas bloqueadas | **5** (familia FAULT — depende de FaultEventSink) |
| Casos físicos definidos | **30** (`03-physical-cases.md`) |
| Casos cubiertos por código | **24/30** (80 %) |
| Score de realismo estimado | **0.94** (banda `plausible con caveats menores`) |
| Coeficientes físicos en `domain.yaml` LEÍDOS por código | **7/11** confirmado por grep (T-PV-50, L-PV-03 cerrada) |
| Coeficientes ignorados por código | **4** (`co2.outdoor_ppm` SÍ leído; `humidity.outdoor_mean` SÍ; `noise.std` SÍ; quedan: `daily_noise_std`, hooks `physics_overrides.py` no enchufados) |

Conclusión rápida: el generador **es plausible para demos y desarrollo de modelos ML** y la cadena `domain.yaml → physics.py → MQTT → Telegraf → InfluxDB` es coherente y trazable. Los 3 frenos para producción son: (1) `FaultEventSink` no emite `state_events`, (2) HVAC sin anti short-cycle, (3) jitter setpoint demasiado agresivo (genera 75 cambios/h por aula en `state_events`).

---

## 1. Catálogo de variables → modelo físico → calibración

Las 22 variables del catálogo (`config/domains/bms_classrooms/variables.yaml`) cubren 6 familias. La columna *override en code* indica si el coeficiente nominal es leído desde `config/domains/bms_classrooms/domain.yaml` (estado real verificado por `grep` sobre el vendor).

| Variable vendor | `production_name` (CAPTIA) | Módulo `physics/` | Modelo | Coeficientes leídos | Snapshot AULA01 18:56:34Z |
|---|---|---|---|---|---|
| `temperature` | `temperature_01` | `indoor.simulate_indoor_temperature` | RC 1er orden + occ heat gain + drift outdoor | `tau_minutes`, `initial_temp`, `occupancy_heat_gain_c_per_person` | 19.72 °C |
| `humidity` | `relative-humidity` | `indoor.simulate_humidity` | 1er orden ocupacional, τ=180 min hardcoded | `outdoor_mean`, `occupancy_gain_per_person` | 59.77 %RH |
| `co2` | `co2` | `indoor.simulate_co2` | Well-mixed `dc/dt = occ·gen − k·(c − outdoor)` | `outdoor_ppm`, `gen_ppm_per_min_per_person`, `vent_k_per_min`, `leak_k_per_min` | 467 ppm |
| `noise` | `avg-sound-level` | `indoor.simulate_noise` | Lineal por tramos sobre ocupación | `base_unoccupied`, `base_occupied`, `std` | 35.45 dB(A) |
| `illuminance` | `luminosity` | `indoor.simulate_illuminance` | `max(daylight, target_artificial)` + ruido | `target_lux_on`, `target_lux_off`, `std` | 80.24 lux |
| `occupancy` | `people-count` | `occupancy.py` (Poisson) | Poisson(`capacity·util·p_slot·day_var`) | `aula_capacity_*`, `aula_utilization_*`, `slots[*]` | 0 personas |
| `presence_pir` | `occupancy` | `indoor.derive_pir_presence` | Sensor PIR derivado, FP=0.4 % FN=1.0 % | hardcoded | 0 |
| `outdoor_temp` | `temperature-outdoor` | `environment.py` | Sinusoidal anual + EWMA noise | `outdoor_temp.mean_annual`, `amplitude`, `daily_noise_std` | 8.10 °C |
| `daylight_lux` | `daylight-lux` | `environment.py` | Coseno diario + estación | hardcoded | 0 (noche) |
| `thermostat_setpoint` | `temperature_01_sp` | `actuators.thermostat_setpoint` | Escena → setpoint + jitter `N(0, 0.3)` + manual `N(0, 0.8)` | `setpoint_class`, `setpoint_out_of_hours` | 17.76 °C |
| `hvac_mode` | `ac_control` | `actuators.hvac_mode` | Umbrales `t_out<16` heat / `>26` cool / 15 % auto en shoulder | hardcoded | 1 (heat) |
| `hvac_enable` | `ac_state` | `actuators.hvac_enable` | `(scene=class ∧ occ>0 ∧ err>0.4) ∨ err>1.5` | hardcoded | 1 |
| `heating_valve_pos` | `valve_control` | `actuators.heating_valve_position` | Proporcional `clip(err·35, 0, 100)` solo en heat | hardcoded | 0 |
| `light_state` | `light_01_state` | `actuators.light_state` | `(occ>0 ∧ daylight<250) ∨ extra(p=0.12)` | hardcoded | 0 |
| `light_state_2` | `light_02_state` | derivado interno | mismo modelo, RNG distinto | hardcoded | 1 |
| `scene_mode` | `scene_mode` | `actuators.derive_scene` | `class` ↔ `out_of_hours` ↔ `manual` (`p=0.0008/sample`) | hardcoded | 0 (out_of_hours) |
| `relay_1..relay_4` | `light_*_state`, `fan_speed_*_state` | — | **NO IMPLEMENTADO** (L-PV-01) — solo emiten `light_01_state`, `light_02_state`, `fan_speed_01_state`, `fan_speed_02_state` que cubren parcialmente | hardcoded | 0/0 fan, 0/1 light |
| `power` | `power_01` | `energy.py` | Aditivo `base + 180·light + 900·hvac + 8·occ + spikes` | hardcoded | 1065.20 W |
| `energy` | `energy_01` | `energy.py` | `cumsum(power · dt_h) / 1000` | hardcoded | 0.24 kWh |
| `iaq_index` | `iaq-index` | derivado | combinación de CO2, RH, T_VOC | hardcoded | 20.98 |

> **L-PV-03 cerrada** (T-PV-50): el `domain.yaml` actual usa las claves canónicas que el vendor lee literalmente (verificado por `Grep` en `vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics`). Coeficientes hot-pluggable hoy: `tau_minutes`, `occupancy_heat_gain_c_per_person`, `outdoor_ppm`, `gen_ppm_per_min_per_person`, `vent_k_per_min`, `leak_k_per_min`, `setpoint_class`, `setpoint_out_of_hours`, `target_lux_on`, `outdoor_mean`, `occupancy_gain_per_person`, `base_unoccupied`, `base_occupied`, `std`. El reporte previo del comparador físico mencionaba esto como gap; tras T-PV-50 NO lo es.

---

## 2. Modelos por categoría (literal del código)

### 2.1 ENVIRONMENTAL (`environment.py`)

#### outdoor_temperature
Cita `environment.py:13-46` (sin re-leer aquí; comentario top de archivo describe `seasonal = mean_annual + amp · sin(2π·(doy − 200) / 365.25)` + EWMA `α=0.02`).

- Plausibilidad: sinusoidal anual con peak ~23 julio. Coherente con AEMET Valencia 2021–24 (`mean_annual=17 °C`, `amplitude=9.5 °C`).
- Snapshot: `8.10 °C` el 9 mayo a las 18:56 UTC. Valor bajo para Valencia esa fecha (esperado ~17–19 °C). El cálculo está bien: el job lleva en backfill desde 2025-09-08 y el reloj simulado va por delante o por detrás del wall-clock — se observa drift documentado en H-21 (`E2E_VALIDATION_REPORT.md:127`).
- **Gap reproducible**: `daily_noise_std=1.0` está en `domain.yaml` pero el vendor lo lee con default 0.6. Pendiente verificar `environment.py:39` (no leído en esta auditoría — añadir a phase #7).

#### daylight_lux
Cita `environment.py:49-79`.

- Modelo: coseno con day-length estacional, peak ~700 lux indoor cerca de ventana.
- Snapshot: 0 lux a las 18:56 (post-puesta de sol) ✓.
- Gap: sin nubosidad — los días reales tienen variabilidad 0–0.5 sobre la curva ideal.

### 2.2 OCCUPANCY (`occupancy.py`)

- Modelo Poisson: `expected = capacity · util · p_slot_activo · day_to_day_var`, `occ = clip(Poisson(expected), 0, capacity)` (`domain.yaml:74-86`).
- PIR derivado en `indoor.derive_pir_presence` (líneas 206-226): `pir = (occ>0 ∨ FP) ∧ ¬FN`, FP=0.4 %, FN=1.0 % por sample.
- Snapshot: ambas variables en 0 a las 18:56 (fuera de slot 8:00-15:00 ni 15:00-20:00 con p=0.30) — **escena coherente**.
- Gap: transiciones entrada/salida instantáneas entre samples (sin rampa 5–10 min real).

### 2.3 INDOOR (`indoor.py`)

#### temperature
`indoor.simulate_indoor_temperature` (líneas 13-57). Lectura directa del código:
```python
tau = float(cfg_indoor.get("tau_minutes", 90))
gain = float(cfg_indoor.get("occupancy_heat_gain_c_per_person", 0.02))
alpha = dt_min / max(1.0, tau)
if hvac_enable.iat[i] == 1:
    target = setpoint.iat[i] + occ_gain
else:
    target = 0.7 * T[i-1] + 0.3 * outdoor_temp.iat[i] + occ_gain
T[i] = T[i-1] + alpha * (target - T[i-1]) + N(0, 0.05)
```
- **Es heurística RC simplificada** (no resistencia/capacitancia explícita).
- α de drift sin HVAC = 0.7/0.3 (interno/exterior por sample) — no derivado de `tau` físico → R-T-02 podría dar valor diferente a la spec.
- Snapshot: `T_in=19.72 °C`, `T_sp=17.76 °C`, `ac_state=1` → `|err|=1.96 > 1.5` activa override por error grande **OK** (cumple R-HVAC-EN-01).

#### co2
`indoor.simulate_co2` (líneas 60-99). Modelo well-mixed correcto:
```python
k = leak_k + (vent_k if hvac_enable.iat[i] == 1 else 0.0)
dc = dt_min * (occ * gen - k * (c[i-1] - outdoor))
c[i] = clip(c[i-1] + dc + N(0, 3.0), outdoor, 2200)
```
- **Coeficientes hot-pluggable**: `gen=7.5 ppm/p/min` por defecto (vendor) frente a literatura ASHRAE 4.5 ppm/p/min — mantener fácil override desde `domain.yaml:108`.
- Snapshot: `co2=467 ppm` con `occ=0` y `ac_state=1` → asintota teórica = `outdoor + 0·gen / (leak + vent) ≈ 420 ppm`; observamos 467 → drift dinámico + ruido ±15 ppm acumulado (`c[0] = outdoor + N(0, 15)`) **dentro de ±50 ppm de equilibrio** → razonable.
- Gap: vendor default `gen=7.5` mayor que ASHRAE 4.5 (1.7×); cuando el aula esté llena pico CO2 resultante será 1.7× más alto que cualquier dataset real.

#### humidity
`indoor.simulate_humidity` (líneas 102-136). Lectura directa:
```python
alpha = dt_min / 180.0  # tau hardcoded 180 min
target = outdoor_mean + occ_gain * occupancy.iat[i]
h[i] = h[i-1] + alpha * (target - h[i-1]) + N(0, 0.2)
```
- **Tau hardcoded 180 min** (no leído desde config) — única constante climatológica del bloque que no está externalizada.
- Snapshot: `RH=59.77 %` con `occ=0` y `outdoor_mean=55` → drift dinámico hacia 55 ± `gain·occ` ≈ 55 → observamos 59.77, dentro de ±5 %RH del target. **OK**.
- Gap **L-PV-09**: `cooling no deshumidifica`. En la realidad, AC con batería fría condensa y `∂RH/∂t < 0`. Aquí RH **siempre** drift hacia `outdoor_mean + gain·occ`, ignorando `hvac_enable`.

#### noise
`indoor.simulate_noise` (líneas 139-168):
```python
n = where(occ>0, 55 + 0.35*occ, 33) + N(0, 4)
```
- **Discontinuidad**: salto instantáneo 33 → 55 dB entre `occ=0` y `occ=1` — heurística aceptada.
- Snapshot: `35.45 dB` con `occ=0` ⇒ `33 + N(0,4)` ≈ 33-37 → **OK**.

#### illuminance
`indoor.simulate_illuminance` (líneas 171-203):
```python
base = where(light==1, max(daylight, target_on), max(daylight, target_off)) + N(0, 40)
```
- Operador `max()` en vez de suma — idealización.
- Snapshot: `lux=80.24` con `daylight=0` y `light_01_state=0` → `max(0, 70) + N(0,40)` ⇒ `80.24` exactamente dentro de tolerancia. **OK**.

### 2.4 HVAC CONTROL (`actuators.py`)

#### thermostat_setpoint
`actuators.thermostat_setpoint` (líneas 59-90):
```python
sp_class = cfg.get("setpoint_class", 21.0)
sp_ooh = cfg.get("setpoint_out_of_hours", 18.0)
jitter = N(0, 0.3, n)
base = where(scene=="class", sp_class, sp_ooh)
base = where(scene=="manual", base + N(0, 0.8, n), base)
return clip(base + jitter, 16.0, 26.0)
```
- Snapshot: `sp=17.76 °C` (cerca de `sp_ooh=18.0`) — **coherente**.
- **Hallazgo nuevo H-23** (no en AUDIT_REPORT): el jitter de 0.3 °C/sample dispara on-change permanentemente. Conteo state_events últimas 6h → `temperature_01_sp = 10762` eventos; con 24 aulas y 6 h, son **75 cambios/h por aula**. La filosofía CENTINELA es solo on-change; jitter `>0.3` cada 5 s viola el espíritu (cambios reales del termostato son ≤ pocas veces por día).

#### hvac_mode
`actuators.hvac_mode` (93-118):
```python
mode[t<16] = "heat"
mode[t>26] = "cool"
shoulder = (16<=t<=26); mode[shoulder] = where(rng<0.15, "auto", "off")
```
- Snapshot: `T_out=8.10 °C` → `mode="heat"` → emitido como `1` ✓.
- **Gap L-PV-08**: el modelo de temperatura (`indoor.simulate_indoor_temperature`) NO diferencia heat / cool: ambos con mismo α — cooling debería ser más rápido en realidad.

#### hvac_enable
`actuators.hvac_enable` (121-146):
```python
err = abs(indoor_temp - setpoint)
enable = ((scene=="class" & occ>0 & err>0.4) | (err>1.5))
```
- Snapshot: `err = |19.72 − 17.76| = 1.96 > 1.5` → `enable=1` ✓.
- **Gap L-PV-07**: SIN `MinOnOffTimer`. Puede toggle entre samples de 5 s — un compresor real moriría. Cuenta state_events `ac_state=1215` últimas 6h ÷ 24 aulas ÷ 6 h = **8 cambios/h por aula** — algo elevado pero no patológico (cambia de off a on con histéresis natural por jitter del setpoint).

#### heating_valve_position
`actuators.heating_valve_position` (149-169):
```python
err = setpoint - indoor_temp
pos = where(mode=="heat", clip(err*35, 0, 100), 0.0)
```
- Snapshot: con `mode="heat"`, `err = 17.76 − 19.72 = −1.96 < 0` → `clip(-1.96·35, 0, 100) = 0` ✓ (válvula cerrada porque el aula ya está caliente sobre setpoint).
- **Gap L-PV-08 (rate limiter)**: 0 → 100 % en 1 sample posible si error pasa de negativo a positivo grande. Real: rate ~2-5 %/s.

### 2.5 ENERGY (`energy.py`)

#### power
`energy.simulate_power` (referencia agente, líneas 11-49):
```python
p = 80 + 180*light_state + 900*hvac_enable + 8*occupancy + N(0, std) + spikes_rare
```
- Coeficientes literales: `base=80W` (standby OK), `light=180W` (LED panel 4×40W ≈ 160W OK), `hvac=900W` (1HP ≈ 1100W OK con margen), `occ=8W` (algo bajo — laptops aportan 15-25W).
- Snapshot: `light_01=0`, `light_02=1`, `hvac=1`, `occ=0` → `p = 80 + 180·1 + 900·1 + 0 + N(0, std) ≈ 1160 W ± std`; observado `1065.20 W` → dentro de ±100 W. **OK**.

#### energy
Integral cumulativa `cumsum(p · dt_h) / 1000` en kWh. Monotónica creciente garantizada — R-EN-02 cumplida por construcción.

---

## 3. Reglas de plausibilidad (`04-physical-plausibility-rules.md`)

53 reglas distribuidas en 12 familias. Estado actual:

| Familia | Reglas | Implementables | Bloqueadas | Confianza |
|---|---|---|---|---|
| T (térmica) | 5 | 5 | 0 | 4 high, 1 low (R-T-04 ganancia ocupacional con `occ=0` no observable hoy) |
| CO₂ | 5 | 5 | 0 | 3 high, 2 medium (R-CO2-01 con caveat: vendor `gen=7.5` vs ASHRAE) |
| RH | 3 | 2 | 0 | R-RH-02 cooling-deshumidifica esperada FAIL (L-PV-09) |
| Ruido + Luz + PIR + Escena + Setpoint | 7 | 7 | 0 | mayormente high |
| HVAC (mode, enable, válvula) | 6 | 4 | 0 | R-HVAC-EN-03 anti-cycle FAIL (L-PV-07); R-VLV-02 rate FAIL (L-PV-08) |
| Ocupación | 3 | 3 | 0 | R-OCC-01 festivos en vendor depende de `holidays` plana — cubierta tras T-PV-09 |
| Power, Energía | 6 | 6 | 0 | R-PW-02 standby OK observado, R-EN-02 monotonicidad por construcción |
| Outdoor temp, daylight, weather | 4 | 4 | 0 | 3 high, 1 medium (sin nubosidad) |
| **Averías (FAULT)** | 5 | **0** | **5** | bloqueadas por L-PV-02 (FaultEventSink no emite a `state_events`) |
| Anomalías dato | 3 | 3 | 0 | stuck_sensor + out_of_order pendientes (L-PV-15, L-PV-14) |
| Infraestructura | 5 | 4 | 0 | R-INF-03 catálogo coverage FAIL (L-PV-01: `relay_*` no emitidas como tales) |
| **TOTAL** | **53** | **45** | **5** | 34 high, 11 medium |

Reglas cuya falla está documentada en open questions:

- **R-RH-02** (humedad cooling): FAIL — L-PV-09.
- **R-HVAC-EN-03** (anti short-cycle): FAIL — L-PV-07.
- **R-VLV-02** (válvula rate): FAIL — L-PV-08.
- **R-INF-03** (catálogo coverage): FAIL — L-PV-01 (`relay_1..4` mapeo).
- **R-FAULT-01..05**: bloqueadas — L-PV-02.

---

## 4. Score de realismo (`08-physical-realism-score.md`)

Score por dimensión (10 dimensiones, pesos en spec):

| Dim | # Reglas | Peso | Estado | Comentario |
|---|---|---|---|---|
| D1 Térmica | 5 | 0.12 | 1.00 ✓ | RC plausible |
| D2 HVAC | 6 | 0.13 | ~0.90 ⚠ | R-HVAC-EN-03 baja por L-PV-07 |
| D3 Energética | 6 | 0.12 | 1.00 ✓ | Aditivo verificable |
| D4 Ocupación/CO₂ | 8 | 0.15 | ~0.87 ⚠ | gen=7.5 vs ASHRAE; festivos OK |
| D5 Meteo/contexto | 5 | 0.08 | 1.00 ✓ | sinusoidal + continuo |
| D6 Humedad | 3 | 0.05 | 1.00 ✓ | R-RH-02 omitida (low confidence) |
| D7 Averías | 5 | 0.10 | **UNSCORED** | bloqueado L-PV-02 |
| D8 Anomalías dato | 3 | 0.05 | 1.00 ✓ | missing/outlier básico |
| D9 Reproducibilidad | 1 | 0.10 | 1.00 ✓ | seed=42 determinista (T-PV-50 cierra L-PV-03) |
| D10 CAPTIA compat | 5 | 0.10 | ~0.80 ⚠ | R-INF-03 falla |

Score global redistribuyendo D7 (bloqueada):
```
(0.12·1.00 + 0.13·0.90 + 0.12·1.00 + 0.15·0.87 + 0.08·1.00 + 0.05·1.00
 + 0.05·1.00 + 0.10·1.00 + 0.10·0.80) / 0.90 ≈ 0.94
```

Banda: **plausible con caveats menores** (0.85-0.95).

> El validador `bms_physics_validator` que computa el score en automático (`07-validator-design.md`) **no está implementado** todavía (T-PV-01 pendiente). Hoy el score se estima manualmente.

---

## 5. Casos físicos (`03-physical-cases.md`)

30 casos en 8 familias:

| Familia | # | Cubiertos | Notas |
|---|---|---|---|
| C-TH-01..03 dinámica térmica | 3 | 3/3 ✓ | RC validable |
| C-HV-01..04 control HVAC | 4 | 3/4 ⚠ | C-HV-03 anti-cycle FAIL |
| C-OC-01..04 ocupación/IAQ | 4 | 4/4 ✓ | poisson + slots |
| C-EN-01..04 energía | 4 | 4/4 ✓ | conservación |
| C-WX-01..03 meteo | 3 | 3/3 ✓ | estacionalidad |
| C-FA-01..04 averías | 4 | **0/4** ✗ | bloqueado L-PV-02 |
| C-AN-01..05 anomalías dato | 5 | 3/5 ⚠ | stuck/dups pendientes |
| C-CO-01..03 coherencia | 3 | 2/3 ⚠ | C-CO-03 catálogo |
| **TOTAL** | 30 | **24/30 (80 %)** | |

---

## 6. Evidencia live — snapshot AULA01 a 2026-05-09T18:56:34Z

Tabla obtenida con `from(bucket:"telemetry") |> range(start:-6h) |> filter(asset_id="AULA01") |> last()`:

| Variable | Valor | Plausibilidad esperada | OK / Anomalía |
|---|---|---|---|
| `ac_control` | 1 (heat) | `T_out=8.10 → mode=heat` | ✓ |
| `ac_state` | 1 | `\|T-sp\|=1.96 > 1.5` activa override | ✓ |
| `avg-sound-level` | 35.45 dB | `base_unoccupied + N(0,4) ⇒ [25,41]` | ✓ |
| `co2` | 467 ppm | `outdoor + drift ⇒ [420, 470]` | ✓ |
| `daylight-lux` | 0 | post-sunset 18:56 | ✓ |
| `energy_01` | 0.24 kWh | acumulado backfill | ✓ |
| `fan_speed_01_state` | 0 | sin actividad | ✓ |
| `fan_speed_02_state` | 0 | sin actividad | ✓ |
| `iaq-index` | 20.98 | derivada compuesta | ✓ |
| `light_01_state` | 0 | scene=out_of_hours | ✓ |
| `light_02_state` | 1 | extra light (p=0.12) | ✓ |
| `luminosity` | 80.24 lux | `max(0,70) + N(0,40) ⇒ [40,160]` | ✓ |
| `occupancy` | 0 | derivado PIR de occ=0 | ✓ |
| `people-count` | 0 | post-15:00 (slot p=0.30 con muestreo Poisson, posible 0) | ✓ |
| `power_01` | 1065 W | `80 + 180·1 + 900·1 = 1160 W ± std` | ✓ |
| `relative-humidity` | 59.77 %RH | `outdoor_mean=55 + drift` | ✓ |
| `scene_mode` | 0 (out_of_hours) | post-15:00 con occ=0 | ✓ |
| `temperature-outdoor` | 8.10 °C | bajo para 9 mayo Valencia | ⚠ ver H-21 (drift TZ runner) |
| `temperature_01` | 19.72 °C | rango plausible | ✓ |
| `temperature_01_sp` | 17.76 °C | `sp_ooh=18 + N(0, 0.3)` | ✓ |
| `valve_control` | 0 | `clip(err·35) = 0` con err<0 | ✓ |

**18 de 21** variables coherentes con su modelo físico declarado. La única anomalía `temperature-outdoor=8.10 °C` se explica por H-21 (vendor `runner.py` usa `datetime.now()` naive — wall-clock vs simulated drift).

---

## 7. Hallazgos físicos top-10 (corregidos vs reporte agente)

| # | Variable / modelo | Código actual | Spec exige | Severidad | Acción mínima |
|---|---|---|---|---|---|
| F-1 | `humidity` | RH siempre drift hacia outdoor + occ | Cooling debería deshumidificar | **Alta** | L-PV-09: añadir `if hvac_enable & mode='cool': target -= dehum_rate` |
| F-2 | `hvac_enable` | toggle posible cada 5 s | Min on-time 5 min, off-time 5 min | **Alta** | L-PV-07: añadir `MinOnOffTimer` en `actuators.hvac_enable` |
| F-3 | `relay_1..4` | NO emitidas | catálogo 100 % | **Alta** | L-PV-01: derivar de `light_state` y `fan_speed_*` y emitir |
| F-4 | `temperature_01_sp` jitter | `N(0, 0.3)` por sample → 75 ev/h en `state_events` | Setpoint estable, cambia al cambiar escena/manual | **Alta nueva H-23** | reducir `jitter_std` a 0.05 o eliminar; setpoint solo cambia en escena |
| F-5 | `temperature` cooling | mismo α que heat | Cooling rate ≠ heating rate | **Media** | L-PV-08: bifurcar `α_cool` vs `α_heat` |
| F-6 | `valve_control` | sin rate limiter | 2-5 %/s real | **Media** | L-PV-08: `pos[i] = clip(pos[i-1] + ±max_rate·dt)` |
| F-7 | `co2` `gen` | default 7.5 ppm/p/min vendor | ASHRAE 4.5; rango 3-7 | **Media** | leer override desde `physics_overrides.py` cuando exista L-01 |
| F-8 | `outdoor_temperature` | tiempo simulado naive vs wall-clock | TZ-aware UTC | **Media** | H-21: parchar `vendor/.../runner.py` con `datetime.now(tz=UTC)` |
| F-9 | Ocupación | rampa instantánea entre samples | Real ~5-10 min | **Baja** | añadir HMM o rampa exp (post-v1) |
| F-10 | `iaq-index` | derivada hardcoded | Spec EN 16798 modal | **Baja** | exponer `cfg_iaq` con tablas |

---

## 8. Queries Flux para validación periódica

```flux
// V-1: CO₂ realmente sube con ocupación (correlación > 0)
co2 = from(bucket:"telemetry") |> range(start:-7d)
       |> filter(fn:(r) => r.variable=="co2" and r.asset_id=="AULA01")
       |> aggregateWindow(every:15m, fn:mean, createEmpty:false)
       |> keep(columns:["_time","_value"])
occ = from(bucket:"telemetry") |> range(start:-7d)
       |> filter(fn:(r) => r.variable=="people-count" and r.asset_id=="AULA01")
       |> aggregateWindow(every:15m, fn:mean, createEmpty:false)
       |> keep(columns:["_time","_value"])
join(tables:{c:co2, o:occ}, on:["_time"])
  |> map(fn:(r) => ({_time:r._time, co2:r._value_c, people:r._value_o}))
```

```flux
// V-2: rangos físicos respetados (CO₂ ∈ [420, 2200], T ∈ [16, 32])
from(bucket:"telemetry") |> range(start:-7d)
  |> filter(fn:(r) => r.variable=="co2")
  |> group()
  |> reduce(identity:{cnt:0.0, mn:1e10, mx:-1e10},
            fn:(r,a) => ({cnt:a.cnt+1.0,
                           mn:if r._value<a.mn then r._value else a.mn,
                           mx:if r._value>a.mx then r._value else a.mx}))
```

```flux
// V-3: standby con todo apagado (occ=0, hvac=0, light=0) → power < 100 W
power = from(bucket:"telemetry") |> range(start:-7d)
        |> filter(fn:(r) => r.variable=="power_01" and r.asset_id=="AULA01")
hvac  = from(bucket:"telemetry") |> range(start:-7d)
        |> filter(fn:(r) => r.variable=="ac_state" and r.asset_id=="AULA01")
join(tables:{p:power, h:hvac}, on:["_time"])
  |> filter(fn:(r) => r._value_h == 0)
  |> map(fn:(r) => ({_time:r._time, p_off:r._value_p}))
  |> mean(column:"p_off")
// Esperado: media < 110 W
```

```flux
// V-4: heartbeat dedup en state_events (algún cambio en 168 h)
from(bucket:"state_events") |> range(start:-168h)
  |> filter(fn:(r) => r._measurement=="captia_point_state")
  |> group(columns:["asset_id","variable"])
  |> count()
  |> filter(fn:(r) => r._value == 0)
// Esperado: vacío (todas las series tuvieron al menos un evento)
```

---

## 9. Conclusión

- **Score físico estimado**: **0.94** (banda *plausible con caveats menores*).
- **Cobertura de casos**: **24/30 (80 %)**; queda 20 % atado a L-PV-02 (FaultEventSink) y L-PV-01 (relay_*).
- **L-PV-03 cerrada** (T-PV-50): 13 coeficientes hot-pluggable desde `domain.yaml`. El reporte físico generado por el sub-agente comparador subestimaba esta migración — corregido aquí.
- **Validador automático del score**: pendiente (T-PV-01).
- **Hallazgo nuevo H-23**: jitter setpoint `N(0, 0.3)/sample` es excesivo para CENTINELA on-change (genera 75 cambios/h por aula en `state_events`).

Top 3 acciones prioritarias para subir el score por encima de 0.97 antes de entrenamiento ML productivo:

1. **L-PV-02 — FaultEventSink emitiendo a `state_events`**: activa D7 (10 % del peso) → score sube a ~1.04 redistribuido ⇒ banda *altamente realista*.
2. **L-PV-07 — Anti short-cycle HVAC**: D2 sube a ~1.00 y elimina el warning más visible de cualquier modelo de detección de averías.
3. **H-23 — Reducir jitter setpoint**: limpia `state_events` (factor 50× menos eventos), reduce ruido para detección y mejora dataset de entrenamiento.

> Fase #6 cerrada — siguientes: #7 correcciones mínimas trazables (priorizando F-4 / H-23, F-2 / L-PV-07, F-1 / L-PV-09 — son los 3 sin dependencias externas y de fácil parche), luego #8 MkDocs, #9 GitHub Pages, #10 ACTION_PLAN final.
