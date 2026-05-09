# 05 — Validación mediante simulaciones controladas (Fase 5)

## Contexto

Validar realismo físico requiere **aislar efectos**. Esta spec define experimentos con un único factor cambiado a la vez, ejecutables como pares de runs (control vs treatment) con seeds reproducibles.

**Convención**: `Exp-<FAMILIA>-NN`. Cada experimento se asocia a una hipótesis falseable y a una o más reglas (`04-*`).

**Mecanismo**: cada experimento describe una receta YAML que extiende `bms_v1_demo.yaml` o `bms_v1_caseB_consumption.yaml` con overrides. El validador (`07-validator-design.md`) ejecuta los pares y aplica `acceptance_logic`.

## Familia A — Térmica

### Exp-TH-1 — Step de setpoint

```yaml
experiment_id: Exp-TH-1
hypothesis: |
  Un cambio de setpoint de +5°C provoca convergencia de T_indoor con tau ≈ 90 min.
controlled_variables:
  - outdoor_temp = 18°C constante (override config: amplitude=0)
  - occupancy = 0 (override schedule: p_occupancy=0 todo el día)
  - hvac_enable = 1 forzado por step
  - mode = heat
changed_variable: thermostat_setpoint (de 19°C a 24°C en t=2h)
expected_response: |
  T_indoor[t=2h] = 19°C (estable).
  T_indoor[t=2h+90min] ≈ 19 + 5·(1-e^-1) = 22.16°C.
  T_indoor[t=2h+270min] ≈ 19 + 5·(1-e^-3) = 23.75°C.
observation_window: 8 horas (cubre 4·tau).
acceptance_logic: |
  Tras step, T_indoor[t=2h+90min] ∈ [21.5, 22.8]°C (±0.7°C tolerancia).
  T_indoor[t=2h+270min] ∈ [23.3, 24.2]°C.
required_seed: 42
reproducibility_notes: |
  Forzar HVAC enable manualmente requiere o (a) un override de actuators.hvac_enable
  (no soportado en modelo actual) o (b) configurar setpoint inicial muy alto para
  garantizar enable=1 todo el tiempo.
  Recomendación práctica: setpoint inicial 19°C, T_indoor inicial 17°C → enable=1 garantizado.
links: PQ-01, R-T-01, R-T-03
```

### Exp-TH-2 — Drift al exterior con HVAC off

```yaml
experiment_id: Exp-TH-2
hypothesis: |
  Sin HVAC, T_indoor decae exponencialmente a T_outdoor con tau=90 min.
controlled_variables:
  - outdoor_temp = 5°C constante (invierno extremo)
  - occupancy = 0
  - thermostat_setpoint forzado a -10°C (garantiza enable=0 vía no error útil)
changed_variable: hvac_enable (forzado=0 desde t=0)
expected_response: |
  T_indoor[t=0] = 20.5°C (initial_temp default).
  T_indoor decae:
  T(t) = 5 + (20.5-5)·exp(-t/90) [donde t en min]
  T(90 min) ≈ 5 + 15.5·0.368 ≈ 10.7°C.
  T(180 min) ≈ 5 + 15.5·0.135 ≈ 7.1°C.
acceptance_logic: |
  T_indoor[90min] ∈ [9.5, 11.5]°C.
  T_indoor[180min] ∈ [6.5, 8.5]°C.
observation_window: 6 horas.
required_seed: 42
reproducibility_notes: |
  Forzar enable=0 en modelo actual requiere setpoint extremo (poco realista).
  Alternativa: instrumentar el path con un override en el plug-in (extensión específica para tests).
links: PQ-02, R-T-02
```

### Exp-TH-3 — Pulso de ocupación (par A/B)

```yaml
experiment_id: Exp-TH-3
hypothesis: |
  Δoccupancy ≥ 20 personas durante 60 min con HVAC off provoca ΔT_indoor ≥ 0.4°C atribuible.
runs:
  run_A:
    controlled_variables:
      - outdoor_temp = 18°C constante
      - hvac_enable = 0 forzado
      - occupancy = 0 (override schedule)
  run_B:
    controlled_variables:
      - outdoor_temp = 18°C constante
      - hvac_enable = 0 forzado
      - occupancy = 25 (forzado constante)
changed_variable: occupancy entre runs.
expected_response: |
  ΔT(t) = T_B(t) - T_A(t).
  Modelo: target_B = 0.7·T_prev + 0.3·18 + 0.5 (de occ_gain·25).
  Estado estacionario: T_B → 18·0.3 + T_B·0.7 + 0.5 → T_B = 19.67°C aprox.
  T_A → 18°C (steady).
  ΔT_steady ≈ 1.67°C (no 0.5; el modelo usa 0.7/0.3 que da equilibrio distinto).
acceptance_logic: |
  ΔT(t=60min) ∈ [0.3, 1.5]°C (banda generosa por modelo simplificado).
  Signo: positivo (presencia eleva T).
observation_window: 3 horas por run.
required_seed_run_A: 42
required_seed_run_B: 42 (mismo seed, distinta señal — el RNG generará trazas distintas pero comparables)
reproducibility_notes: |
  Esto es un experimento pareado. Para análisis correcto debe usar mismo seed
  en ambos runs y diferenciar solo por la entrada `occupancy`.
  Atención: el plug-in inicializa rng_aula = default_rng(seed + asset_idx) — ambos
  runs verán las mismas trayectorias de exterior y ruido, lo cual es lo deseado.
links: PQ-03, R-T-04
```

## Familia B — HVAC

### Exp-HV-1 — Comparativa modos heat vs cool

```yaml
experiment_id: Exp-HV-1
hypothesis: |
  El generador trata heat y cool simétricamente respecto al setpoint en simulate_indoor_temperature
  (refleja L-PV-08 — gap de modelo).
runs:
  run_heat:
    controlled_variables:
      - outdoor_temp = 5°C
      - thermostat_setpoint = 22°C
      - occupancy = 0
  run_cool:
    controlled_variables:
      - outdoor_temp = 32°C
      - thermostat_setpoint = 22°C
      - occupancy = 0
expected_response: |
  Mode debería ser "heat" en run_heat y "cool" en run_cool.
  Time-to-band(0.5°C) debería ser similar en ambos (pero en realidad cooling es más lento por capacidad limitada).
acceptance_logic: |
  Verificar mode == "heat" en run_heat (>95% samples).
  Verificar mode == "cool" en run_cool (>95%).
  Comparar time_to_band(setpoint, 0.5°C).
  Si time_to_band_heat ≈ time_to_band_cool → confirmar L-PV-08 (modelo simétrico).
  Si time_to_band_cool > 1.5·time_to_band_heat → modelo refleja capacidad cooling limitada (mejora).
observation_window: 6 horas.
required_seed: 42
links: PQ-06, R-HVAC-MODE-01, L-PV-08
notes: experimento de DIAGNÓSTICO, no pass/fail estricto.
```

### Exp-HV-2 — Ciclo enable/disable cerca de threshold

```yaml
experiment_id: Exp-HV-2
hypothesis: |
  Sin anti short-cycle, hvac_enable oscila rápido cuando |T-setpoint| ≈ threshold (0.4°C en clase).
controlled_variables:
  - outdoor_temp = 18°C constante
  - thermostat_setpoint = 21°C constante
  - scene_mode = "class" forzado
  - occupancy = 15 forzado constante
changed_variable: ninguno (ejecutar 8h y observar dinámica natural).
expected_response: |
  Si modelo SIN anti-cycle (actual): runs cortos < 5 min son frecuentes; short_cycle_ratio > 0.10.
  Si modelo CON anti-cycle (futuro): p10(run_lengths) ≥ 5 min; short_cycle_ratio < 0.05.
acceptance_logic: medir short_cycle_ratio. Reportar.
observation_window: 8 horas.
required_seed: 42
links: PQ-07, R-HVAC-EN-03, L-PV-07
notes: experimento de DIAGNÓSTICO de gap conocido.
```

## Familia C — IAQ

### Exp-IAQ-1 — Pulso CO₂ con ventilación on/off

```yaml
experiment_id: Exp-IAQ-1
hypothesis: |
  Con HVAC off, CO₂ sube a velocidad ≈ 7.5·occ ppm/min. Con HVAC on, baja con tau=14 min.
runs:
  run_off:
    controlled_variables:
      - hvac_enable = 0 forzado durante todo el run
      - occupancy = 20 forzado durante 1h
  run_on:
    controlled_variables:
      - hvac_enable = 1 forzado tras t=30 min (con CO₂ ya subido)
      - occupancy = 20 forzado durante 1h
expected_response: |
  run_off:
    co2(t=30 min) ≈ 420 + 30·(7.5·20 - 0.01·(c-420))·promediado
    Con c inicial 420: tras 30 min co2 ≈ 1500-2200 ppm (saturación esperable).
  run_on (tras transición):
    co2 baja con tau=14 min hacia asíntota gen·occ/(leak+vent) + outdoor
    = (7.5·20 / 0.07) + 420 = 2143 + 420 = 2563 → clipea a 2200 (gap permanece).
    PERO el ratio dco2/dt cambia: pre 0→1 era >+5 ppm/min, post es ~0 o negativo.
acceptance_logic: |
  run_off: pendiente CO₂ en ventana [10min, 30min] > 5 ppm/min.
  run_on: pendiente CO₂ en ventana [40min, 50min] (post-on) < pendiente run_off mismo intervalo.
observation_window: 90 min.
required_seed: 42
links: PQ-10, PQ-11, R-CO2-01, R-CO2-02
```

### Exp-IAQ-2 — Decadencia nocturna

```yaml
experiment_id: Exp-IAQ-2
hypothesis: |
  Tras 6h con occupancy=0, CO₂ decae a outdoor_ppm + 30 ppm.
controlled_variables:
  - occupancy = 0 desde t=0 (override schedule todo el run a 0)
  - hvac_enable = 0
  - co2 inicial alto: forzar c[0] = 1500 ppm (vía override de cfg_co2 si se permite, o esperar 30 min con occ alto antes de t=0)
expected_response: |
  c(t) = 420 + (1500-420)·exp(-t/100min)
  c(180 min) = 420 + 1080·0.165 = 598 ppm
  c(360 min) = 420 + 1080·0.027 = 449 ppm
  c(420 min, 7h) ≈ 425 ppm.
acceptance_logic: |
  c[t=6h] ≤ 500 ppm.
  c[t=7h] ≤ 470 ppm.
observation_window: 8 horas.
required_seed: 42
links: PQ-12, R-CO2-03
```

## Familia D — Calendario y ocupación

### Exp-CAL-1 — Día lectivo vs festivo

```yaml
experiment_id: Exp-CAL-1
hypothesis: |
  Festivo (e.g., 2025-12-25 Navidad) tiene occupancy ≈ 0 todo el día.
runs:
  run_lectivo:
    controlled_variables:
      - simulation.start = 2025-09-15 (lunes lectivo) 00:00
      - simulation.end = 2025-09-15 23:59
  run_festivo:
    controlled_variables:
      - simulation.start = 2025-12-25 00:00
      - simulation.end = 2025-12-25 23:59
expected_response: |
  run_lectivo: mean(occupancy_diaria) ≥ 5.
  run_festivo: mean(occupancy_diaria) ≤ 1.
acceptance_logic: |
  Diff(mean_lectivo - mean_festivo) ≥ 4 personas.
required_seed: 42
links: PQ-14, R-OCC-01
notes: |
  CRITICAL — verificar si calendar usado efectivamente coincide con holidays en domain.yaml.
  Si NO (por L-PV-06), este experimento revelará el bug.
```

### Exp-CAL-2 — Lunes vs sábado (mismo mes)

```yaml
experiment_id: Exp-CAL-2
hypothesis: |
  Sábado tiene occupancy < 10% del lunes equivalente.
runs:
  run_lunes:
    controlled_variables:
      - start: 2025-10-13 (lunes) 00:00
      - end: 2025-10-13 23:59
  run_sabado:
    controlled_variables:
      - start: 2025-10-18 (sábado) 00:00
      - end: 2025-10-18 23:59
expected_response: |
  mean(occupancy_lunes) > 10·mean(occupancy_sabado).
acceptance_logic: ratio ≥ 5 (banda generosa).
required_seed: 42
links: PQ-15, R-OCC-02
```

## Familia E — Meteo y estaciones

### Exp-WX-1 — Verano vs invierno

```yaml
experiment_id: Exp-WX-1
hypothesis: |
  Mediana T_outdoor en julio difiere de enero por al menos 14°C (amplitud 9.5 → 19°C swing).
runs:
  run_julio:
    controlled_variables:
      - start: 2026-07-15 00:00
      - end: 2026-07-21 23:59 (1 semana)
  run_enero:
    controlled_variables:
      - start: 2026-01-15 00:00
      - end: 2026-01-21 23:59
expected_response: |
  mean(T_outdoor_julio) ≈ 17 + 9.5·sin(2π·196/365.25 - 200/365.25) ≈ 26°C.
  mean(T_outdoor_enero) ≈ 8°C.
  Diff ≈ 18°C.
acceptance_logic: diff ∈ [12, 22]°C.
required_seed: 42
links: PQ-23, R-WX-01
```

## Familia F — Averías

### Exp-FA-1 — Sensor drift activo (cuando wiring exista)

```yaml
experiment_id: Exp-FA-1
hypothesis: |
  Activar sensor_drift produce un evento marcado en state_events y bias en la señal afectada.
status: BLOCKED por L-PV-02.
runs:
  run_baseline:
    config: bms_v1_demo.yaml
    controlled: faults_enabled=false
  run_drift:
    config: bms_v1_demo.yaml
    controlled: faults_enabled=true, sensor_drift.probability_per_day=1.0 (1 evento/día garantizado)
expected_response: |
  En run_drift: state_events tiene al menos 1 marca con variable=fault.sensor_drift.
  Signal afectada (e.g., temperature) muestra bias creciente durante las 24h del episodio.
acceptance_logic: |
  count_events(state_events, variable=fault.sensor_drift) ≥ 1.
  Bias acumulado al final del episodio: ≥ 0.3°C respecto a run_baseline.
required_seed: 42
links: PQ-26, R-FAULT-01
when_unblocked: implementar tras L-PV-02 resuelto.
```

### Exp-FA-2 — Valve stuck (cuando wiring exista)

```yaml
experiment_id: Exp-FA-2
hypothesis: |
  valve_stuck mantiene heating_valve_pos constante durante 60 min.
status: BLOCKED por L-PV-02.
runs: análogo Exp-FA-1 con valve_stuck.probability_per_day=1.0.
expected_response: |
  En episodio: std(heating_valve_pos[event_window]) ≤ 1%.
  Pre/post: std normal.
acceptance_logic: ratio std_during/std_outside ≤ 0.05.
links: R-FAULT-02
```

### Exp-FA-3 — Fan failure (cuando wiring + variables existan)

```yaml
experiment_id: Exp-FA-3
hypothesis: |
  fan_failure cae power eléctrico aunque hvac_enable=1.
status: BLOCKED por L-PV-02 (wiring) y L-PV-01 (fan_speed_*_state no existe).
expected_response: |
  Power_actual < expected (deficit ~900 W) durante episodio con hvac_enable=1.
links: R-FAULT-03
```

## Familia G — Anomalías de dato

### Exp-AN-1 — Random missing rate

```yaml
experiment_id: Exp-AN-1
hypothesis: |
  Con p_missing=0.01, el rate observado coincide con configurado dentro de ±0.5%.
controlled_variables:
  - anomalies.p_missing = 0.01
  - duration: 7 días
expected_response: |
  count(emitted) / count(expected) ≈ 0.99 ± 0.005.
acceptance_logic: |
  |actual_rate - 0.01| ≤ 0.005.
  Con N ≈ 70 aulas · 21 vars · 12 samples/h · 24h · 7d ≈ 2.5M samples → SE ≈ 0.0001.
required_seed: 42
links: PQ-31, R-AN-01
```

### Exp-AN-2 — Outlier rate y flag

```yaml
experiment_id: Exp-AN-2
hypothesis: |
  Outliers tienen quality=OUTLIER y rate ≈ p_outlier.
controlled_variables:
  - anomalies.p_outlier = 0.005
expected_response: |
  count(quality=OUTLIER) / count(total) ≈ 0.005 ± 0.0005.
  Magnitud de outliers: |value - rolling_mean| > 3·rolling_std en p99.
acceptance_logic: |
  |actual - p_outlier| ≤ 0.0005.
  Magnitud detectable.
links: PQ-32, R-AN-02
```

### Exp-AN-3 — Burst missing distribution

```yaml
experiment_id: Exp-AN-3
hypothesis: |
  Burst missing produce gaps con duración en burst_duration_range.
controlled_variables:
  - anomalies.burst_missing_prob_per_day = 1.0 (forzar al menos 1 burst/día)
  - anomalies.burst_duration_range = [5, 15]
expected_response: |
  Distribución de gaps: moda en [5, 15] samples.
acceptance_logic: ≥ 80% de gaps detectados ∈ rango.
links: PQ-33, R-AN-03
```

## Familia H — Coherencia infraestructura

### Exp-INF-1 — Reproducibilidad seed

```yaml
experiment_id: Exp-INF-1
hypothesis: Hash sha256 de salida idéntico con mismo seed.
runs:
  run_1: seed=42
  run_2: seed=42 (mismo)
expected_response: |
  hash(output_run_1) == hash(output_run_2).
acceptance_logic: igualdad estricta.
links: PQ-25, R-INF-02
```

### Exp-INF-2 — Schema canónico

```yaml
experiment_id: Exp-INF-2
hypothesis: 100% DataPoints emitidos cumplen schema canónico.
controlled_variables: cualquier escenario.
expected_response: |
  scripts/verify_canonical_schema.sh PASS.
  ContractValidator (cuando se instancie) reporta 0 errors.
acceptance_logic: 0 violations en N samples.
links: PQ-35, R-INF-01
```

### Exp-INF-3 — DST handling

```yaml
experiment_id: Exp-INF-3
hypothesis: |
  Día de cambio DST (último domingo de marzo y octubre) tiene 23h o 25h en la salida.
runs:
  run_dst_marzo: simulation.start=2026-03-29 00:00 → 2026-03-29 23:59 (Europe/Madrid → 23h efectivas)
  run_dst_octubre: simulation.start=2026-10-25 00:00 → 2026-10-25 23:59 (25h efectivas)
expected_response: |
  count(samples_run_marzo) == ceil(23·60/freq).
  count(samples_run_octubre) == floor(25·60/freq).
acceptance_logic: igualdad estricta o explicación documentada del comportamiento del clock.
links: PQ-40, R-INF-05
notes: probablemente revele bug — Europe/Madrid handling no inspeccionado en detalle.
```

## Tabla resumen de experimentos

| ID | Familia | Pareado | Bloqueado | Duración total |
|----|---------|---------|-----------|----------------|
| Exp-TH-1 | Térmica | No | No | 8 h |
| Exp-TH-2 | Térmica | No | Workaround needed | 6 h |
| Exp-TH-3 | Térmica | Sí (A/B) | No | 3 h × 2 |
| Exp-HV-1 | HVAC | Sí (heat/cool) | No | 6 h × 2 |
| Exp-HV-2 | HVAC | No | No | 8 h |
| Exp-IAQ-1 | IAQ | Sí (off/on) | No | 90 min × 2 |
| Exp-IAQ-2 | IAQ | No | No | 8 h |
| Exp-CAL-1 | Calendar | Sí (lectivo/festivo) | No | 24 h × 2 |
| Exp-CAL-2 | Calendar | Sí (lunes/sábado) | No | 24 h × 2 |
| Exp-WX-1 | Weather | Sí (jul/ene) | No | 7 d × 2 |
| Exp-FA-1 | Faults | Sí | Sí (L-PV-02) | 24 h × 2 |
| Exp-FA-2 | Faults | Sí | Sí | 24 h × 2 |
| Exp-FA-3 | Faults | Sí | Sí (L-PV-01/02) | 24 h × 2 |
| Exp-AN-1 | Anomalies | No | No | 7 d |
| Exp-AN-2 | Anomalies | No | No | 7 d |
| Exp-AN-3 | Anomalies | No | No | 7 d |
| Exp-INF-1 | Infra | Sí (seed×2) | No | trivial |
| Exp-INF-2 | Infra | No | No | trivial |
| Exp-INF-3 | Infra | Sí | No | 24 h × 2 |

**Total: 19 experimentos**, 11 pareados, 3 bloqueados (faults).

## Mecanismo de ejecución

Cada experimento se materializa como:

1. **Receta YAML** en `tests/physics_validation/experiments/<exp_id>.yaml` (cuando se implemente):
   ```yaml
   experiment_id: Exp-TH-1
   base_config: config/projects/bms_v1_demo.yaml
   runs:
     - name: control
       overrides:
         simulation.start: "2026-01-15T00:00:00"
         simulation.duration_hours: 8
         physics.outdoor_temp.amplitude: 0
         physics.outdoor_temp.mean_annual: 18
   acceptance:
     - rule: R-T-01
       threshold: q99 ≤ 0.5
   ```

2. **Runner** (`extensions/bms_physics_validator/experiments_runner.py`, futuro): carga receta, ejecuta runs, aplica reglas, reporta JSON.

3. **CI gate**: experimentos no-bloqueados corren en `make test-physics` (futuro). Bloqueados se skipean con marker `@pytest.mark.skip(reason="L-PV-02")`.

## Limitaciones del aproach

- **Forzar señales** (e.g., `hvac_enable=0` o `occupancy=25 constante`) requiere overrides que el modelo actual no expone vía YAML. Hay 2 caminos: (a) añadir `force_overrides` al `BMSDomainPlugin` (modifica vendor — vía PATCH); (b) fixture programática que reemplace funciones físicas durante el test (más invasivo pero menos riesgoso).
- **Experimentos de averías bloqueados** hasta resolver L-PV-02. Documentados aquí para que sean inmediatamente ejecutables cuando el wiring esté.
- **Significancia estadística** depende de N. Para experimentos con bandas estrechas (Exp-AN-1), N debe ser grande (≥ días de simulación).

## Cobertura cruzada

Cada regla de `04-*` tiene al menos 1 experimento que la valida (cobertura completa) excepto las reglas de tipo `infrastructure` (R-INF-*) que se validan con scripts existentes (`verify_canonical_schema.sh`).
