# 04 — Reglas de plausibilidad física (Fase 4)

## Contexto

Reglas concretas que el validador (`07-validator-design.md`) puede ejecutar mecánicamente. Cada regla es **falseable** (tiene patrón de violación claro) y tiene **confidence_level** explícito.

**Decisión de diseño** (consenso usuario): plausibilidad ahora con literatura (ASHRAE 62.1, EN 16798, AEMET, EN ISO 13790) + comportamiento observable en código. Cuando llegue ground-truth real (L-01), se sube confidence y se ajustan thresholds.

**Convención**:
- ID: `R-<FAMILIA>-NN`. Familias: T (térmica), CO2, RH (humedad), N (ruido), LX (illuminance), LS (light_state), PIR, SC (scene), SP (setpoint), HVAC-MODE, HVAC-EN, VLV (válvula), OCC (ocupación), PW (power), EN (energía), OT (outdoor temp), DL (daylight), WX (weather), WD (weather dependency), FAULT (averías), AN (anomalías de dato), INF (infraestructura).

## Tipos de regla

```text
rule_type:
  monotonicity         — la serie debe crecer o decrecer monotónicamente
  rate_of_change       — |x[i] - x[i-1]| ≤ threshold
  causal_lag           — y[t] responde a x[t-Δ] con lag ∈ [Δ_min, Δ_max]
  correlation          — corr(x, y) ≥ threshold en ventana
  anti_correlation     — corr(x, y) ≤ -threshold
  state_consistency    — cuando estado A, señal B debe estar en conjunto S
  conservation_or_balance — Σx ≈ y dentro de tolerancia
  bounded_response     — y(t) ≤ y_max o y(t) ∈ [a, b] tras condición
  hysteresis           — distribución de longitudes de runs respeta mínimos
  seasonality          — patrón cíclico (anual, semanal, diario) presente
  occupancy_dependency — variable correlacionada con occupancy
  weather_dependency   — variable correlacionada con outdoor_temp / season
  fault_signature      — durante evento de avería, patrón distintivo presente
  anomaly_signature    — distribución de quality flags / gaps respeta config
  infrastructure       — schema, naming, freq, tz cumplidos
```

## Familia T — Dinámica térmica

### R-T-01 — Rate of change razonable

```yaml
rule_id: R-T-01
rule_type: rate_of_change
physical_meaning: La inercia térmica impide saltos > 0.5°C/min.
applicable_when: hvac_enable estable durante ventana (no transición).
signals_required: [temperature]
expected_pattern: |
  q99(|temperature.diff() / dt_min|) ≤ 0.5°C/min
violation_pattern: salto > 0.5°C/min sostenido.
tolerance_strategy: tolerancia 1.0°C/min en transiciones HVAC enable 0↔1 (excluir ±2 samples alrededor).
validation_window: 1 hora rolling.
severity: warning
confidence_level: high (literatura RC + modelo explícito).
implementation_hint: |
  diff = temperature.diff() / (dt_min)
  exclude_transitions = mask hvac_enable.diff() != 0 con padding ±2
  q99 sobre filtered.
```

### R-T-02 — Drift al exterior con HVAC off

```yaml
rule_id: R-T-02
rule_type: causal_lag
physical_meaning: Sin HVAC, T_indoor tiende a T_outdoor con tau característico.
applicable_when: hvac_enable=0 sostenido ≥ 90 min y ΔT_outdoor estable.
signals_required: [temperature, outdoor_temp, hvac_enable]
expected_pattern: |
  Tras 90 min con HVAC off:
  T_indoor[t0+90min] - T_outdoor ≈ (T_indoor[t0] - T_outdoor) · exp(-1)
  Es decir: gap_t1 / gap_t0 ∈ [0.30, 0.45].
violation_pattern: gap_t1/gap_t0 ≈ 1 (T_indoor no decae) o > 1 (diverge).
tolerance_strategy: ratio ∈ [0.20, 0.55] (banda más generosa).
validation_window: ventanas de 90 min con HVAC off.
severity: warning
confidence_level: high.
implementation_hint: |
  off_windows = identificar runs de hvac_enable=0 con duración ≥ 90 min.
  Para cada uno: calcular gap inicial y a 90 min. Comprobar ratio.
```

### R-T-03 — Convergencia al setpoint

```yaml
rule_id: R-T-03
rule_type: bounded_response
physical_meaning: Tras 3·tau con HVAC enabled estable, T en banda de ±0.5°C alrededor del setpoint.
applicable_when: hvac_enable=1 sostenido ≥ 270 min y setpoint estable.
signals_required: [temperature, thermostat_setpoint, hvac_enable]
expected_pattern: |
  En p95 de samples elegibles: |temperature - setpoint| ≤ 0.5°C.
violation_pattern: error sostenido > 1°C tras estabilización.
tolerance_strategy: 1°C banda (incluye occ_gain y ruido).
validation_window: 1 día.
severity: warning
confidence_level: medium (modelo estabiliza pero ruido N(0, 0.05) acumulado puede sesgar).
```

### R-T-04 — Ganancia ocupacional separable

```yaml
rule_id: R-T-04
rule_type: correlation
physical_meaning: ΔT atribuible a occupancy debe ser distinguible del drift exterior.
applicable_when: requiere experimento controlado (run pareado A/B). Ver C-TH-03 y `05-controlled-simulation-validation.md` Exp-TH-3.
signals_required: [temperature_runA, temperature_runB, occupancy_runA=0, occupancy_runB=N>20]
expected_pattern: |
  En t = 30 min: T_B - T_A ≥ 0.3°C, signo positivo.
violation_pattern: T_B - T_A ≤ 0 o no significativo (CI95 cruzando 0).
severity: warning
confidence_level: medium (ratio señal/ruido marginal en ventana de 30 min — ampliar a 60 min mejora).
notes: solo aplicable en framework de experimentos pareados, no en datos puros.
```

### R-T-05 — Sin oscilación periódica espuria

```yaml
rule_id: R-T-05
rule_type: bounded_response
physical_meaning: La temperatura no debe oscilar a frecuencia HVAC (sin overshoot/undershoot persistente).
applicable_when: ventana ≥ 6 horas con HVAC sostenido enabled.
signals_required: [temperature]
expected_pattern: |
  std(temperature[steady-state]) ≤ 0.4°C.
  No hay pico significativo en FFT a frecuencia ≈ 1/(min_on_off_cycle).
violation_pattern: std > 0.7°C, pico FFT a freq HVAC.
severity: info
confidence_level: low (sin anti-cycle, modelo actual puede oscilar — esta regla detecta el síntoma de L-PV-07).
```

## Familia CO₂

### R-CO2-01 — Buildup proporcional a ocupación

```yaml
rule_id: R-CO2-01
rule_type: occupancy_dependency
physical_meaning: |
  En ausencia de ventilación, dCO2/dt = occ·gen - leak·(c-outdoor).
applicable_when: hvac_enable=0 sostenido ≥ 30 min, occupancy estable.
signals_required: [co2, occupancy, hvac_enable]
expected_pattern: |
  Regresión OLS de Δco2/Δt vs occupancy:
  pendiente positiva ∈ [3, 12] ppm/(min·persona) (literatura ASHRAE 4.5; modelo 7.5; banda generosa).
  R² > 0.5 si N ≥ 30.
violation_pattern: pendiente ≤ 0 o R² ~ 0.
tolerance_strategy: aceptar pendiente 1-15 ppm/(min·persona).
validation_window: ventanas de 30 min con HVAC off.
severity: warning
confidence_level: medium (modelo divergente con literatura — gen=7.5 vs ASHRAE 4.5 — flag esperado).
implementation_hint: |
  Identificar ventanas hvac_enable=0 sostenido ≥ 30 min.
  Computar pendiente CO₂ (regresión sobre 6 samples a freq=5min).
  Asociar a media occupancy de la ventana.
  Acumular pares (occ_mean, slope) y regresar.
```

### R-CO2-02 — Ventilación reduce CO₂

```yaml
rule_id: R-CO2-02
rule_type: causal_lag
physical_meaning: |
  Activar HVAC añade vent_k → tau pasa de 100 min a 14 min.
applicable_when: transición hvac_enable 0→1 con occupancy estable y co2 elevado (>700 ppm).
signals_required: [co2, hvac_enable, occupancy]
expected_pattern: |
  Pendiente Δco2/Δt en ventana [t-15min, t-1] vs [t+1, t+15min]:
  slope_post < slope_pre - 5 ppm/min (atenuación significativa).
violation_pattern: slope_post ≥ slope_pre.
tolerance_strategy: requerir transición clara, mín 10 transiciones para análisis estadístico.
validation_window: 30 min alrededor de cada transición.
severity: warning
confidence_level: high.
```

### R-CO2-03 — Asíntota al outdoor

```yaml
rule_id: R-CO2-03
rule_type: bounded_response
physical_meaning: Sin ocupación durante 6h, CO₂ → outdoor.
applicable_when: occupancy=0 sostenido ≥ 6h.
signals_required: [co2, occupancy]
expected_pattern: |
  En último sample del run: co2 ≤ outdoor_ppm + 50 (banda incluye ruido y leak lento).
violation_pattern: co2 > outdoor + 100 ppm.
tolerance_strategy: outdoor_ppm = 420 (default vendor).
validation_window: ventanas nocturnas (00:00-06:00).
severity: warning
confidence_level: medium (depende de leak_k=0.01 actual — ver L-PV-11).
```

### R-CO2-04 — Sin clipping artificial sospechoso

```yaml
rule_id: R-CO2-04
rule_type: bounded_response
physical_meaning: |
  CO₂ está clipeado a [outdoor, 2200] (indoor.py:97). Saturación a 2200 sostenida indica que el modelo
  superó capacidad razonable. En aulas reales, CO₂ > 2000 ppm es severo pero ocurre.
applicable_when: cualquier ventana.
signals_required: [co2]
expected_pattern: |
  Tiempo en saturación c=2200 < 5% del tiempo total con occupancy>0.
violation_pattern: > 20% del tiempo en saturación → modelo de ventilación insuficiente.
severity: info
confidence_level: high.
```

### R-CO2-05 — Float floor

```yaml
rule_id: R-CO2-05
rule_type: bounded_response
expected_pattern: co2 ≥ outdoor_ppm en 100% de samples.
violation_pattern: co2 < outdoor_ppm (bug clipping).
severity: error
confidence_level: high (clip explícito en código).
```

## Familia RH (humedad)

### R-RH-01 — Bounded range

```yaml
rule_id: R-RH-01
rule_type: bounded_response
expected_pattern: humidity ∈ [10, 90] %RH siempre.
violation_pattern: fuera de rango (no debería con clip).
severity: error
confidence_level: high.
```

### R-RH-02 — Anti-correlación con cooling (ground-truth required)

```yaml
rule_id: R-RH-02
rule_type: anti_correlation
physical_meaning: |
  HVAC en modo cool DEBE deshumidificar (la batería fría condensa).
  En modelo actual NO se cumple (L-PV-09).
applicable_when: ventana con hvac_mode=cool y hvac_enable=1 sostenido.
signals_required: [humidity, hvac_mode, hvac_enable]
expected_pattern: |
  Pendiente de humidity en ventana cool-on debería ser negativa (∂RH/∂t < -0.05 %RH/min al inicio).
violation_pattern: |
  Pendiente positiva o nula → modelo no deshumidifica → flag L-PV-09.
severity: warning
confidence_level: low (es regla "should fail", refleja gap del modelo).
notes: |
  Esta regla es intencionalmente esperada FALLAR contra el código actual. Documentada como
  diagnóstico, no como pass/fail. Cuando se implemente cooling con dehumidification, sube confidence.
links: L-PV-09
```

### R-RH-03 — Coupling occupancy

```yaml
rule_id: R-RH-03
rule_type: occupancy_dependency
physical_meaning: |
  Personas exhalan vapor de agua. Modelo aplica +0.08 %RH/persona como target shift.
expected_pattern: |
  Ventana de 1h: ΔRH ≈ 0.08 · Δoccupancy_mean (con tau=180min, atenuado).
  Estado estacionario con occ=20 vs occ=0: ΔRH ≈ 1.6 %RH detectable.
severity: info
confidence_level: medium.
```

## Familia N (ruido)

### R-N-01 — Salto en transiciones occupancy

```yaml
rule_id: R-N-01
rule_type: state_consistency
physical_meaning: |
  Modelo actual produce salto instantáneo de 33 a ~55 dB cuando occupancy pasa de 0 a 1.
  Realista sería rampa.
expected_pattern: documentar — no es violación del modelo, sino limitación.
violation_pattern: | (no aplicable; el modelo HACE el salto).
severity: info
confidence_level: high.
notes: regla es DIAGNÓSTICO, mide ratio de transiciones con salto > 20 dB instantáneo.
```

## Familia LX (illuminance)

### R-LX-01 — Indoor lux ≥ daylight

```yaml
rule_id: R-LX-01
rule_type: state_consistency
expected_pattern: |
  illuminance ≥ max(daylight_lux, target_off=70) - tolerancia 50 lux (ruido).
violation_pattern: indoor lux < daylight_lux (físicamente imposible salvo persianas).
severity: error
confidence_level: high.
```

### R-LX-02 — Coherencia con light_state

```yaml
rule_id: R-LX-02
rule_type: state_consistency
expected_pattern: |
  Cuando light_state=1 (proxy: detectable por jump en illuminance ~+500 lux):
  illuminance ≥ target_on - 3·std = 550 - 120 = 430 lux.
  Cuando light_state=0: illuminance ≤ daylight_lux + 3·std.
severity: warning
confidence_level: medium (light_state es interno, no emitido — proxy detection necesaria).
```

## Familia LS (light_state, interno)

### R-LS-01 — Light apagada en aula vacía

```yaml
rule_id: R-LS-01
rule_type: state_consistency
applicable_when: occupancy=0 sostenido.
expected_pattern: |
  Cuando occupancy=0, light_state debe ser 0 (modelo lo garantiza estructuralmente).
violation_pattern: indoor illuminance > daylight + 100 lux con occ=0 (signo de luz encendida sin gente).
severity: warning
confidence_level: high.
```

## Familia PIR

### R-PIR-01 — Tasa FP/FN respetada

```yaml
rule_id: R-PIR-01
rule_type: anomaly_signature
expected_pattern: |
  En ventana grande:
  FP_rate := P(presence_pir=1 | occupancy=0) ≈ 0.004 ± 0.001.
  FN_rate := P(presence_pir=0 | occupancy>0) ≈ 0.01 ± 0.003.
severity: info
confidence_level: high (verificable desde indoor.py:222-223).
```

## Familia SC (scene)

### R-SC-01 — Coherencia con calendario

```yaml
rule_id: R-SC-01
rule_type: state_consistency
expected_pattern: |
  scene == "class" → school_mask == True AND occupancy > 0.
  scene == "manual" → respetar duración (run length entre 15 y 90 samples).
severity: warning
confidence_level: high.
```

## Familia SP (setpoint)

### R-SP-01 — Setpoint en banda

```yaml
rule_id: R-SP-01
rule_type: bounded_response
expected_pattern: thermostat_setpoint ∈ [16, 26] °C (clip explícito).
severity: error
confidence_level: high.
```

## Familia HVAC-MODE

### R-HVAC-MODE-01 — Modo coherente con T_outdoor

```yaml
rule_id: R-HVAC-MODE-01
rule_type: state_consistency
expected_pattern: |
  Distribución de hvac_mode por bucket de outdoor_temp:
  T<16°C → mode=heat ≥ 95%
  T>26°C → mode=cool ≥ 95%
  16≤T≤26 → mode ∈ {off (~85%), auto (~15%)}
severity: warning
confidence_level: high.
```

## Familia HVAC-EN

### R-HVAC-EN-01 — Activación por error

```yaml
rule_id: R-HVAC-EN-01
rule_type: state_consistency
expected_pattern: |
  Para cada sample i, calcular expected_enable según fórmula del código:
  expected = ((scene=="class") AND (occ>0) AND (|T-sp|>0.4)) OR (|T-sp|>1.5)
  Aceptar si mean(actual == expected) ≥ 0.99.
severity: error
confidence_level: high.
```

### R-HVAC-EN-02 — Power coupling

```yaml
rule_id: R-HVAC-EN-02
rule_type: correlation
expected_pattern: |
  median(power | hvac_enable=1) - median(power | hvac_enable=0) ≥ 700 W.
severity: warning
confidence_level: high.
```

### R-HVAC-EN-03 — Anti short-cycle

```yaml
rule_id: R-HVAC-EN-03
rule_type: hysteresis
expected_pattern: |
  RLE de hvac_enable: p10(run_lengths) ≥ 5 min.
  short_cycle_ratio := P(run < 5 min) ≤ 0.05.
violation_pattern: short_cycle_ratio > 0.20.
severity: info
confidence_level: low (modelo actual sin anti-cycle — flag esperado).
notes: regla detecta L-PV-07; pasa cuando se integre MinOnOffTimer.
```

## Familia VLV (válvula)

### R-VLV-01 — Válvula coherente con modo

```yaml
rule_id: R-VLV-01
rule_type: state_consistency
expected_pattern: |
  heating_valve_pos > 0 → hvac_mode == "heat" en 100%.
  hvac_mode != "heat" → heating_valve_pos == 0.
severity: error
confidence_level: high.
```

### R-VLV-02 — Sin saltos (rate limiter)

```yaml
rule_id: R-VLV-02
rule_type: rate_of_change
expected_pattern: |
  |heating_valve_pos[i] - heating_valve_pos[i-1]| ≤ 30%/min.
violation_pattern: salto 0→100% en 1 sample.
severity: info
confidence_level: low (modelo actual no tiene rate limiter — flag esperado).
```

## Familia OCC (ocupación)

### R-OCC-01 — Cero en festivos

```yaml
rule_id: R-OCC-01
rule_type: occupancy_dependency
expected_pattern: |
  Para fechas en periodos vacacionales (Navidad, Pascua, Verano):
  mean(occupancy_diaria) ≤ 1 personas.
severity: error
confidence_level: medium (depende de qué calendario use el path activo — L-PV-06).
```

### R-OCC-02 — Slot horario respetado

```yaml
rule_id: R-OCC-02
rule_type: state_consistency
expected_pattern: |
  Fuera de slots configurados (e.g., 21:00-08:00): occupancy ≈ 0.
  Dentro de slot 08:00-15:00 día lectivo: mean(occupancy) ≥ 5 personas.
severity: warning
confidence_level: high.
```

### R-OCC-03 — Bounded range

```yaml
rule_id: R-OCC-03
rule_type: bounded_response
expected_pattern: occupancy ∈ [0, capacity] donde capacity ∈ [10, ~50].
violation_pattern: occupancy > capacity (bug clip).
severity: error
confidence_level: high.
```

## Familia PW (power)

### R-PW-01 — Descomposición lineal

```yaml
rule_id: R-PW-01
rule_type: conservation_or_balance
expected_pattern: |
  Regresión OLS power ~ light_state + hvac_enable + occupancy:
  intercept ∈ [60, 100] W.
  β_light ∈ [150, 220] W.
  β_hvac ∈ [800, 1100] W.
  β_occ ∈ [5, 15] W/persona.
  R² ≥ 0.85.
severity: warning
confidence_level: high.
```

### R-PW-02 — Standby

```yaml
rule_id: R-PW-02
rule_type: bounded_response
expected_pattern: |
  En samples con occ=0 AND hvac_enable=0 AND light_state=0:
  median(power) ∈ [70, 100] W.
  p99(power) < 200 W (sin spikes).
severity: warning
confidence_level: high.
```

### R-PW-03 — No negativa

```yaml
rule_id: R-PW-03
rule_type: bounded_response
expected_pattern: power ≥ 0.
severity: error
confidence_level: high.
```

## Familia EN (energía)

### R-EN-01 — Conservación

```yaml
rule_id: R-EN-01
rule_type: conservation_or_balance
expected_pattern: |
  En cualquier ventana [t0, t1]:
  |Δenergy_kWh - Σ(power[t0:t1] · dt_h)/1000| / Δenergy_kWh ≤ 0.01 (1%).
severity: error
confidence_level: high.
```

### R-EN-02 — Monotonicidad

```yaml
rule_id: R-EN-02
rule_type: monotonicity
expected_pattern: energy[i+1] ≥ energy[i] siempre.
severity: error
confidence_level: high.
```

### R-EN-03 — Crecimiento razonable

```yaml
rule_id: R-EN-03
rule_type: bounded_response
expected_pattern: |
  Δenergy_diaria_por_aula ∈ [3, 30] kWh (con power medio 100-1300 W).
violation_pattern: > 50 kWh/día/aula (sospechoso de coupling fantasma).
severity: warning
confidence_level: medium.
```

## Familia OT (outdoor temp)

### R-OT-01 — Continuidad

```yaml
rule_id: R-OT-01
rule_type: rate_of_change
expected_pattern: |
  |outdoor_temp[i] - outdoor_temp[i-1]| ≤ 0.5°C/min en p99.9.
severity: warning
confidence_level: high.
```

### R-OT-02 — Bounded range

```yaml
rule_id: R-OT-02
rule_type: bounded_response
expected_pattern: outdoor_temp ∈ [-5, 40] °C en climatología Csa Valencia.
severity: info
confidence_level: medium (modelo actual: amplitud 9.5 → rango efectivo ≈ [-2, 37]).
```

## Familia DL (daylight)

### R-DL-01 — Día/noche

```yaml
rule_id: R-DL-01
rule_type: state_consistency
expected_pattern: |
  daylight_lux = 0 antes de sunrise(doy) y después de sunset(doy).
  Peak ∈ [600, 750] lux alrededor del mediodía solar.
severity: warning
confidence_level: high.
```

## Familia WX (weather)

### R-WX-01 — Estacionalidad

```yaml
rule_id: R-WX-01
rule_type: seasonality
expected_pattern: |
  Mean(outdoor_temp, julio) ∈ [25, 28] °C.
  Mean(outdoor_temp, enero) ∈ [6, 10] °C.
  Day-of-year del peak ∈ [180, 220].
severity: warning
confidence_level: high.
```

## Familia WD (weather dependency)

### R-WD-01 — Energía vs severidad meteorológica

```yaml
rule_id: R-WD-01
rule_type: weather_dependency
expected_pattern: |
  Quintil 5 de severidad (|T_mean_diaria - 19|) → mediana energía diaria > 1.3 · mediana de quintil 1.
severity: info
confidence_level: medium (modelo HVAC step independiente de severidad — solo activación cambia).
```

## Familia FAULT (averías)

### R-FAULT-01 — Sensor drift signature

```yaml
rule_id: R-FAULT-01
rule_type: fault_signature
fault_family: sensor_drift
applicable_when: existe FaultEventSink (L-PV-02 resuelto).
expected_pattern: |
  Durante evento marcado en state_events (variable=fault.sensor_drift, value=1):
  bias_acumulado_signal ≈ severity · drift_rate · t_elapsed.
  Bias en sensor afectado vs otros sensores de control: divergencia monotónica.
violation_pattern: ningún cambio observable en señal durante evento.
severity: error
confidence_level: low (bloqueada por L-PV-02; pasa cuando se cablee).
```

### R-FAULT-02 — Valve stuck signature

```yaml
rule_id: R-FAULT-02
rule_type: fault_signature
fault_family: valve_stuck
expected_pattern: |
  Durante evento: std(heating_valve_pos[event_window]) ≤ 1%.
  Antes y después: std normal (>5% con condiciones similares).
severity: error
confidence_level: low (bloqueada).
```

### R-FAULT-03 — Fan failure signature

```yaml
rule_id: R-FAULT-03
rule_type: fault_signature
fault_family: fan_failure
expected_pattern: |
  Durante evento: power_actual << power_expected (deficit ≈ 900 W cuando hvac_enable=1).
severity: error
confidence_level: low (bloqueada).
```

### R-FAULT-04 — Refrigerant low signature

```yaml
rule_id: R-FAULT-04
rule_type: fault_signature
fault_family: refrigerant_low
expected_pattern: |
  Durante evento: |T_supply - T_return| < 1°C en p95 (vs >5°C sano).
severity: error
confidence_level: low (bloqueada por L-PV-01 + L-PV-02 — variables no existen).
```

### R-FAULT-05 — Cobertura

```yaml
rule_id: R-FAULT-05
rule_type: fault_signature (cobertura)
expected_pattern: |
  N_eventos_FaultInjector == N_marcadores_state_events.
  Δ permitida: 0 (cada evento debe materializarse).
severity: error
confidence_level: low (bloqueada por L-PV-02).
```

## Familia AN (anomalías de dato)

### R-AN-01 — Random missing rate

```yaml
rule_id: R-AN-01
rule_type: anomaly_signature
expected_pattern: |
  count(emitted) ≈ (1 - p_missing) · count(expected).
  Tolerancia: |actual_rate - p_missing| ≤ 0.0005 con N ≥ 10000.
severity: warning
confidence_level: high.
```

### R-AN-02 — Outlier rate y flag

```yaml
rule_id: R-AN-02
rule_type: anomaly_signature
expected_pattern: |
  |count(quality=OUTLIER) / count(total) - p_outlier| ≤ 0.0005 con N grande.
  Outliers están aislados (sin clusters).
severity: warning
confidence_level: high.
```

### R-AN-03 — Burst missing distribution

```yaml
rule_id: R-AN-03
rule_type: anomaly_signature
expected_pattern: |
  Distribución de tamaños de gap muestra moda en [burst_duration_range[0], burst_duration_range[1]].
severity: info
confidence_level: medium (depende de N días simulados).
```

## Familia INF (infraestructura)

### R-INF-01 — Schema canónico

```yaml
rule_id: R-INF-01
rule_type: infrastructure
expected_pattern: |
  100% de DataPoints emitidos cumplen:
  - measurement = captia_point
  - 5 tags: captia_env, domain_id, site_id, asset_id, variable
  - field: value (float)
  - asset_id uppercase, variable lowercase
severity: error
confidence_level: high (verificable con scripts/verify_canonical_schema.sh y ContractValidator).
```

### R-INF-02 — Reproducibilidad

```yaml
rule_id: R-INF-02
rule_type: infrastructure
expected_pattern: |
  Hash sha256 de la salida de 2 runs con mismo seed es idéntico.
severity: error
confidence_level: high.
```

### R-INF-03 — Catálogo coverage

```yaml
rule_id: R-INF-03
rule_type: infrastructure
expected_pattern: |
  Variables emitidas == catálogo (excluyendo light_state interno).
violation_pattern: |
  relay_1..relay_4 en catálogo pero no emitidas (gap conocido — L-PV-01).
severity: warning
confidence_level: high.
```

### R-INF-04 — Frecuencia respetada

```yaml
rule_id: R-INF-04
rule_type: infrastructure
expected_pattern: |
  median(diff(timestamps)) == freq configurado ± 1 ms.
severity: error
confidence_level: high.
```

### R-INF-05 — Timezone respetado

```yaml
rule_id: R-INF-05
rule_type: infrastructure
expected_pattern: |
  Timestamps en Europe/Madrid con DST aplicado.
  Día DST de marzo: 23h cubiertas; de octubre: 25h cubiertas.
severity: warning
confidence_level: medium.
```

## Tabla resumen de reglas

| Familia | # reglas | severity error | severity warning | severity info | confidence high | confidence medium | confidence low |
|---------|---------|---------------|------------------|---------------|----------------|-------------------|----------------|
| T | 5 | 0 | 4 | 1 | 3 | 2 | 0 |
| CO2 | 5 | 1 | 3 | 1 | 3 | 2 | 0 |
| RH | 3 | 1 | 1 | 1 | 2 | 0 | 1 (R-RH-02) |
| N | 1 | 0 | 0 | 1 | 1 | 0 | 0 |
| LX | 2 | 1 | 1 | 0 | 1 | 1 | 0 |
| LS | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| PIR | 1 | 0 | 0 | 1 | 1 | 0 | 0 |
| SC | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| SP | 1 | 1 | 0 | 0 | 1 | 0 | 0 |
| HVAC-MODE | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| HVAC-EN | 3 | 1 | 1 | 1 | 2 | 0 | 1 (R-HVAC-EN-03) |
| VLV | 2 | 1 | 0 | 1 | 1 | 0 | 1 (R-VLV-02) |
| OCC | 3 | 2 | 1 | 0 | 2 | 1 | 0 |
| PW | 3 | 1 | 2 | 0 | 3 | 0 | 0 |
| EN | 3 | 2 | 1 | 0 | 2 | 1 | 0 |
| OT | 2 | 0 | 1 | 1 | 1 | 1 | 0 |
| DL | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| WX | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| WD | 1 | 0 | 0 | 1 | 0 | 1 | 0 |
| FAULT | 5 | 5 | 0 | 0 | 0 | 0 | 5 (todas L-PV-02) |
| AN | 3 | 0 | 2 | 1 | 2 | 1 | 0 |
| INF | 5 | 3 | 1 | 1 | 4 | 1 | 0 |
| **TOTAL** | **53** | **19** | **22** | **12** | **34** | **11** | **8** |

**Distribución**:
- 64% high confidence (verificables hoy contra el código).
- 21% medium (requieren contexto adicional o ground-truth para subir).
- 15% low confidence (todas son bloqueadas por L-PV-01/02/07/09 — están etiquetadas como diagnóstico).

## Cómo subir confidence (cuando llegue calibración real, L-01)

| Confidence inicial | Acción para subir | Reglas afectadas |
|-------------------|-------------------|------------------|
| medium → high | Calibrar gen_ppm_per_min_per_person con datos reales | R-CO2-01 |
| medium → high | Validar amplitud meteo con AEMET 2024-2025 | R-OT-02, R-WX-01 |
| medium → high | Confirmar ranges energéticos con factura real | R-EN-03 |
| low → high | Resolver L-PV-02 (cablear FaultEventSink) | R-FAULT-01..05 |
| low → high | Implementar MinOnOffTimer en HVAC | R-HVAC-EN-03 |
| low → high | Añadir rate limiter a heating_valve_position | R-VLV-02 |
| low → medium | Añadir term cooling_dehumidification a humidity model | R-RH-02 |
