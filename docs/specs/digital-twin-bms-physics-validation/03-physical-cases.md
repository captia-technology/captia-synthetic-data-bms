# 03 — Casos físicos por familia (Fase 3)

## Contexto

Este documento define **familias de comportamiento físico** que el generador debe reproducir, no escenarios cerrados. Cada familia agrupa varios casos físicos con campos uniformes para que el validador (`07-validator-design.md`) pueda iterar sobre ellos.

**Convención de IDs**: `C-<FAMILIA>-NN`.

## Familia 1 — Dinámica térmica

### C-TH-01 — Inercia con HVAC off

```yaml
case_id: C-TH-01
family: thermal_dynamics
physical_principle: |
  La sala se comporta como un sistema RC primer orden. Sin energía añadida (HVAC off, occupancy=0),
  T_indoor tiende exponencialmente a T_outdoor con tau característico (90 min en el modelo).
signals_involved:
  - temperature
  - outdoor_temp
  - occupancy
  - hvac_enable
expected_behavior: |
  Tras un paso de occupancy 25→0 con hvac_enable=0:
  T_indoor decrece (si T_out < T_indoor) o crece (si T_out > T_indoor) hacia T_outdoor.
  En 90 min se cubre ~63% del gap; en 180 min ~86%.
invalid_behavior: |
  T_indoor permanece constante.
  T_indoor se acerca al setpoint (HVAC fantasma).
  T_indoor diverge del exterior.
how_to_validate: |
  Calcular gap_t0 = T_indoor[t0] - T_outdoor[t0].
  Calcular gap_t1 = T_indoor[t0+90min] - T_outdoor[t0+90min].
  Verificar 0.4 ≤ |gap_t1/gap_t0| ≤ 0.5 (ratio esperado e^-1 ≈ 0.37).
minimum_test_duration: 3 horas
confidence_level: high (modelo explícito en código indoor.py:54)
links:
  - PQ-02
  - R-T-02
```

### C-TH-02 — Convergencia al setpoint con HVAC on

```yaml
case_id: C-TH-02
family: thermal_dynamics
physical_principle: |
  Con HVAC enabled y setpoint constante, T_indoor converge al setpoint con tau=90min.
signals_involved:
  - temperature, thermostat_setpoint, hvac_enable
expected_behavior: |
  Si T_indoor[t0] = setpoint - 3°C y hvac_enable=1 sostenido:
  T_indoor[t0+90min] ≈ setpoint - 1.1°C (gap reducido en 63%).
  T_indoor[t0+3h] ≈ setpoint - 0.4°C (banda razonable).
invalid_behavior: |
  T_indoor no llega a setpoint en 5 tau.
  T_indoor oscila > 1°C (overshoot/undershoot persistente).
how_to_validate: |
  Métricas: time_to_band(0.5°C), max_overshoot, std en estado estacionario.
minimum_test_duration: 6 horas (≈ 4·tau).
confidence_level: high
links:
  - PQ-04
  - R-T-03
```

### C-TH-03 — Ganancia ocupacional medible

```yaml
case_id: C-TH-03
family: thermal_dynamics
physical_principle: |
  Cada persona aporta sensible heat ~75W (ASHRAE 55). En el modelo: 0.02°C/persona como target shift.
signals_involved:
  - temperature, occupancy, hvac_enable
expected_behavior: |
  Con HVAC off y occupancy 0→25 sostenida 30 min:
  ΔT_indoor ≥ 0.3°C atribuible (separable de drift exterior).
invalid_behavior: |
  ΔT_indoor independiente de occupancy.
  Magnitud al revés (ΔT negativo con occupancy).
how_to_validate: |
  Run A: occupancy=0 forzado.
  Run B: occupancy=25 forzado.
  ΔT_B(t) - ΔT_A(t) ≥ 0.3°C en t=30 min, escalando con tiempo.
minimum_test_duration: 1 hora.
confidence_level: medium (signal-to-noise ratio ajustado, 0.3°C vs ruido 0.05°C·sqrt(N))
links:
  - PQ-03
  - R-T-04
```

## Familia 2 — Control HVAC

### C-HV-01 — Activación por error térmico

```yaml
case_id: C-HV-01
family: hvac_control
physical_principle: |
  El controlador activa HVAC cuando |T - setpoint| > umbral (0.4°C en clase ocupada, 1.5°C cualquier escena).
signals_involved:
  - hvac_enable, temperature, thermostat_setpoint, scene_mode, occupancy
expected_behavior: |
  En clase ocupada: hvac_enable=1 cuando err > 0.4°C, en p99.
  En out_of_hours: hvac_enable=1 cuando err > 1.5°C, en p99.
  Coexistencia: enable=0 si err < 0.4°C en clase, o err < 1.5°C en otras escenas.
invalid_behavior: |
  enable=1 con err < threshold (consumo fantasma).
  enable=0 con err > threshold sostenido (degradación servicio).
how_to_validate: |
  Para cada sample: clasificar (scene, occupancy, err) → expected_enable.
  Calcular accuracy = mean(actual_enable == expected_enable). Aceptar si ≥ 0.99.
minimum_test_duration: 24 horas.
confidence_level: high (lógica explícita en actuators.py:140-144).
links:
  - PQ-05
  - R-HVAC-EN-01
```

### C-HV-02 — Modo coherente con T_outdoor

```yaml
case_id: C-HV-02
family: hvac_control
physical_principle: |
  Heat en frío, cool en calor, off en intermedios.
signals_involved: hvac_mode, outdoor_temp
expected_behavior: |
  T_out < 16 → mode == "heat" (≥95%)
  T_out > 26 → mode == "cool" (≥95%)
  16 ≤ T_out ≤ 26 → mode ∈ {off (85%), auto (15%)}
invalid_behavior: heat en verano, cool en invierno.
how_to_validate: confusion matrix por bucket de T_outdoor.
minimum_test_duration: 12 meses (cubrir todas las estaciones).
confidence_level: high.
links:
  - PQ-06
  - R-HVAC-MODE-01
```

### C-HV-03 — Sin short-cycle

```yaml
case_id: C-HV-03
family: hvac_control
physical_principle: |
  Compresores y resistencias requieren tiempo mínimo on/off (típicamente 5-10 min) para evitar daño térmico/mecánico.
signals_involved: hvac_enable
expected_behavior: |
  Distribución de duración de runs (consecutivos de 1 o de 0):
  p10 ≥ 5 min en condiciones estables.
  Histograma sin pico en duración == 1 sample.
invalid_behavior: |
  Toggling sample-a-sample (duración modal = 1 sample).
how_to_validate: |
  Run-length encoding sobre hvac_enable. Calcular distribución de longitudes.
  Métrica `hvac_short_cycle_ratio` = (# runs de duración < 5 min) / (# runs total).
  Aceptar si ratio ≤ 0.05.
minimum_test_duration: 24 horas.
confidence_level: medium (modelo actual NO implementa anti-cycle — L-PV-07).
notes: |
  Esta validación está esperada FALLAR en el código actual sin cambios. Es un
  indicador de gap a documentar en `10-implementation-readiness.md`.
links:
  - PQ-07
  - L-PV-07
  - R-HVAC-EN-03
```

### C-HV-04 — Coherencia válvula ↔ modo

```yaml
case_id: C-HV-04
family: hvac_control
physical_principle: |
  La válvula de calefacción solo puede estar abierta si el modo es heat.
signals_involved: heating_valve_pos, hvac_mode
expected_behavior: |
  pos > 0 → mode == "heat" en 100% de samples.
  En cool/off/auto: pos == 0 (con tolerancia 0).
invalid_behavior: cross-talk, válvula abierta en cool.
how_to_validate: filter pos > 0 → grupo by mode → expect singleton "heat".
minimum_test_duration: 1 día por estación.
confidence_level: high (lógica explícita en actuators.py:167).
links:
  - PQ-08
  - R-VLV-01
```

## Familia 3 — Ocupación y calidad de aire

### C-OC-01 — Ocupación durante horario lectivo

```yaml
case_id: C-OC-01
family: occupancy_iaq
physical_principle: |
  En aulas durante horario y día lectivo, occupancy > 0 con probabilidad p_occ del slot.
signals_involved: occupancy, school_mask, p_occupancy_schedule
expected_behavior: |
  En slot 08:00-15:00 día lectivo: media diaria occupancy > 8 personas (capacity 28 · util 0.75 · p_occ 0.85 · day_mult 1.0 ≈ 17, sub-aforo por Poisson).
invalid_behavior: occupancy=0 sostenido durante slot lectivo (excepto agujeros aleatorios cortos).
how_to_validate: |
  Para cada día lectivo: mean(occupancy[slot1]) > 5 (umbral conservador).
  Para cada día no lectivo: mean(occupancy[24h]) ≤ 1.
minimum_test_duration: 7 días (1 semana).
confidence_level: high.
links:
  - PQ-14
  - PQ-15
  - R-OCC-01
```

### C-OC-02 — CO₂ buildup proporcional a ocupación

```yaml
case_id: C-OC-02
family: occupancy_iaq
physical_principle: |
  Cada persona genera ~4.5 ppm/min (ASHRAE) ó 7.5 (modelo actual). Sin ventilación, el CO₂ sube
  proporcionalmente a la ocupación.
signals_involved: co2, occupancy, hvac_enable
expected_behavior: |
  Durante períodos con hvac_enable=0 sostenido y occupancy estable >5:
  pendiente Δco2/Δt = occ · gen - leak·(c - outdoor) ≈ 7.5·occ - 0.01·(c-420) ppm/min
  Para occ=20, c=600: pendiente ≈ 150 - 1.8 ≈ 148 ppm/min (instantáneo).
  Saturación al límite duro 2200 ppm en ~13 min sin ventilación con 20 personas.
invalid_behavior: |
  CO₂ baja con occupancy>0.
  CO₂ no responde a occupancy.
how_to_validate: |
  Regresión lineal Δco2/Δt vs occupancy en ventanas con hvac_enable=0:
  pendiente positiva, R² > 0.5 si N suficiente.
minimum_test_duration: 2 horas con occupancy variable.
confidence_level: high (verificable analíticamente desde indoor.py:91-97).
links:
  - PQ-10
  - PQ-12
  - R-CO2-01
```

### C-OC-03 — Ventilación reduce CO₂

```yaml
case_id: C-OC-03
family: occupancy_iaq
physical_principle: |
  Activar HVAC añade vent_k=0.06/min al término de removal. tau de respuesta cae de 100 a 14 min.
signals_involved: co2, hvac_enable, occupancy
expected_behavior: |
  En transiciones hvac_enable 0→1 con occupancy estable:
  pendiente Δco2/Δt cambia (de >+5 a <+1 ppm/min) en <10 min, o decrece si gen·occ < vent_k·(c-outdoor).
invalid_behavior: |
  Activar HVAC no afecta CO₂.
  CO₂ aumenta más rápido al activar HVAC.
how_to_validate: |
  Detectar transiciones 0→1 de hvac_enable. Calcular pendiente CO₂ pre/post (ventana ±10 min).
  Aceptar si pendiente_post < pendiente_pre.
minimum_test_duration: 24 horas.
confidence_level: high.
links:
  - PQ-11
  - R-CO2-02
```

### C-OC-04 — CO₂ baseline tras horas vacías

```yaml
case_id: C-OC-04
family: occupancy_iaq
physical_principle: |
  Sin generación, leak natural lleva CO₂ a outdoor con tau=100 min.
signals_involved: co2, occupancy
expected_behavior: |
  Tras 6h continuas con occupancy=0 (e.g., madrugadas):
  co2 ≤ outdoor + 30 ppm en p95.
invalid_behavior: |
  co2 > 500 ppm sostenido en ventanas sin ocupación.
how_to_validate: |
  Detectar ventanas de 6h con occupancy=0. Comprobar co2 en último sample.
minimum_test_duration: 1 semana (cubrir 7 noches).
confidence_level: medium (depende de outdoor_ppm config).
links:
  - PQ-12
  - L-PV-11
  - R-CO2-04
```

## Familia 4 — Energía

### C-EN-01 — Conservación power → energy

```yaml
case_id: C-EN-01
family: energy
physical_principle: |
  Energy es la integral temporal de Power. Δenergy = power · Δt.
signals_involved: power, energy
expected_behavior: |
  En cualquier ventana [t0, t1]:
  |Δenergy_kWh - Σ(power · dt_h)/1000| / Δenergy_kWh < 1%.
invalid_behavior: |
  Discrepancia >5%.
  energy decreciendo.
how_to_validate: |
  Recalcular cumsum y comparar con energy(t).
minimum_test_duration: 1 día.
confidence_level: high (cálculo explícito en energy.py:66).
links:
  - PQ-17
  - PQ-18
  - R-EN-01
  - R-EN-02
```

### C-EN-02 — Power coherente con estados

```yaml
case_id: C-EN-02
family: energy
physical_principle: |
  Modelo aditivo. Coeficientes: 80 base + 180 light + 900 hvac + 8 occ + spikes raros.
signals_involved: power, light_state, hvac_enable, occupancy
expected_behavior: |
  Regresión OLS de power vs (1, light_state, hvac_enable, occupancy):
  intercept ≈ 80, β_light ≈ 180, β_hvac ≈ 900, β_occ ≈ 8 ± 1.
  R² alto (>0.85) excluyendo spikes.
invalid_behavior: |
  Coeficientes drift (e.g., β_hvac = 200).
  Intercept incorrecto.
how_to_validate: |
  scikit-learn LinearRegression sobre 24h de datos.
  Comparar coeficientes con expectativa.
minimum_test_duration: 1 semana (variabilidad suficiente).
confidence_level: high.
links:
  - PQ-16
  - R-PW-01
```

### C-EN-03 — Reposo con bajo consumo

```yaml
case_id: C-EN-03
family: energy
physical_principle: |
  Con todo apagado: solo base load + ruido. Standby ~80 W.
signals_involved: power, occupancy, hvac_enable, light_state
expected_evidence: |
  En samples con occupancy=0 AND hvac_enable=0 AND light_state=0:
  median(power) ∈ [70, 100] W.
  p99(power) < 150 W (excluyendo spikes raros).
invalid_behavior: |
  Power medio en reposo > 150 W.
  Consumo HVAC fantasma (>500W con HVAC off).
how_to_validate: filter samples → cohort estadísticas.
minimum_test_duration: 24 horas.
confidence_level: high.
links:
  - PQ-19
  - R-PW-02
```

### C-EN-04 — Consumo escala con clima

```yaml
case_id: C-EN-04
family: energy
physical_principle: |
  Días extremos (T_out < 10 o > 30) tienen mayor demanda HVAC.
signals_involved: energy diario, outdoor_temp diario
expected_behavior: |
  Quintiles de severidad meteorológica diaria (|T_mean - 19|) vs energía diaria/aula:
  pendiente positiva. Días peores → más consumo (al menos +30% vs días moderados con misma occupancy).
invalid_behavior: |
  Consumo independiente del clima.
how_to_validate: |
  Agregado diario. Bucket por severidad. Comparar medianas.
minimum_test_duration: 30 días con variabilidad meteorológica.
confidence_level: medium (modelo HVAC es step independiente de clima en magnitud — solo activación cambia).
links:
  - PQ-20
  - R-WD-01
```

## Familia 5 — Meteo y contexto exterior

### C-WX-01 — Continuidad de T_outdoor

```yaml
case_id: C-WX-01
family: weather_context
physical_principle: |
  Atmósfera tiene inercia (radiación + advección suaves). Saltos artificiales delatan generador.
signals_involved: outdoor_temp
expected_behavior: |
  |T_out[i] - T_out[i-1]| ≤ 0.5°C/min en p99 (con dt=5min: ≤2.5°C).
  std diaria ≤ 8°C (variabilidad razonable).
invalid_behavior: |
  Saltos >5°C entre samples consecutivos.
how_to_validate: |
  diff() series. Calcular percentiles de |diff|.
minimum_test_duration: 1 mes.
confidence_level: high (verificable desde environment.py).
links:
  - PQ-22
  - R-OT-01
```

### C-WX-02 — Estacionalidad

```yaml
case_id: C-WX-02
family: weather_context
physical_principle: |
  Climatología Csa Valencia: media anual 17°C, amplitud 9°C, peak julio.
signals_involved: outdoor_temp
expected_behavior: |
  Mean(T_out, julio) ≈ 26 ± 1°C.
  Mean(T_out, enero) ≈ 8 ± 1°C.
  Phase: día del año del peak ∈ [180, 220].
invalid_behavior: |
  Inversión estacional (calor en enero).
how_to_validate: |
  Agregado mensual. Comparar con AEMET reference o con valores esperados de la fórmula sinusoidal.
minimum_test_duration: 12 meses.
confidence_level: high (fórmula explícita en environment.py:36).
links:
  - PQ-23
  - R-WX-02
```

### C-WX-03 — Daylight día/noche

```yaml
case_id: C-WX-03
family: weather_context
physical_principle: |
  Día solar con duración variable según doy.
signals_involved: daylight_lux, timestamps
expected_behavior: |
  daylight = 0 antes de sunrise(doy) y después de sunset(doy).
  Peak ≤ 700 + 30 lux alrededor del mediodía solar.
invalid_behavior: |
  daylight > 0 a medianoche.
  Peak en hora distinta a mediodía.
how_to_validate: |
  Por día: identificar primer/último sample con lux > 50.
  Comparar con sunrise/sunset esperados.
minimum_test_duration: 4 días (dispersos en estaciones).
confidence_level: high.
links:
  - PQ-24
  - R-DL-01
```

## Familia 6 — Averías físicas

> Estado: bloqueadas por L-PV-01 (catálogo) y L-PV-02 (FaultEventSink no existe). Documentadas para que cuando se cableen sean directamente validables.

### C-FA-01 — Sensor drift (bias acumulativo)

```yaml
case_id: C-FA-01
family: physical_faults
fault_family: sensor_drift
physical_cause: |
  Deriva del calibrador (e.g., NTC envejecido). Bias linealmente creciente, magnitud ε[0.3, 1.0]·drift_rate
  durante el episodio (24h por defecto).
expected_symptoms:
  - bias creciente en sensor afectado (temperature_supply o temperature)
  - sensor diverge respecto a vecinos sanos o respecto a outdoor reference
affected_signals: temperature (o temperature_supply cuando exista)
unaffected_signals: occupancy, power, hvac_enable (lógica de control sigue normal aunque sesgada)
distinguishing_features: |
  vs anomalía outlier: drift es persistente y monotónico; outlier es spike puntual.
  vs valve_stuck: drift afecta lectura, no actuador.
how_to_avoid_false_positives: |
  Comparar siempre contra al menos 1 sensor de referencia (otra aula, outdoor) en la misma ventana.
  Detectar drift solo si la divergencia crece monotónicamente.
validation_strategy: |
  Marca esperada en state_events: variable=fault.sensor_drift, value=1 durante episodio.
  Bias acumulado en sensor afectado ≈ severity · drift_rate · t_elapsed.
  Sin bias en sensores no afectados.
links:
  - PQ-26
  - L-PV-02
  - R-FAULT-01
```

### C-FA-02 — Valve stuck

```yaml
case_id: C-FA-02
family: physical_faults
fault_family: valve_stuck
physical_cause: |
  Atasco mecánico (corrosión, suciedad). La válvula mantiene su última posición durante el episodio (60 min default).
expected_symptoms:
  - heating_valve_pos constante (std ≈ 0) durante episodio
  - T_indoor diverge del setpoint si pos atascada en valor inadecuado
affected_signals: heating_valve_pos, temperature (secundario)
unaffected_signals: hvac_mode, hvac_enable (lógica de control intenta actuar)
distinguishing_features: |
  vs heating off: enable=0 y pos=0 son válidos juntos. Stuck es enable=1 con pos no respondiendo.
how_to_avoid_false_positives: |
  Confirmar enable=1 sostenido durante el episodio. Comparar pos con expected (función de err).
validation_strategy: |
  state_events marca durante 60 min. std(pos[event_window]) < 1%.
  Tras evento: std(pos) > 5% en próxima hora con condiciones similares.
links:
  - PQ-27
  - L-PV-02
  - R-FAULT-02
```

### C-FA-03 — Fan failure

```yaml
case_id: C-FA-03
family: physical_faults
fault_family: fan_failure
physical_cause: |
  Motor del ventilador caído. RPM=0, consumo del ventilador desaparece.
expected_symptoms:
  - power eléctrico cae aunque hvac_enable=1 (resta ~900W)
  - fan_speed_*_state = 0 (cuando exista la señal — actualmente no)
  - T_indoor diverge (sin advección de aire tratado)
affected_signals: power, fan_speed_*_state (futuro)
unaffected_signals: hvac_mode, hvac_enable (sigue intentando)
distinguishing_features: |
  vs HVAC normal off: hvac_enable=1 vs 0.
  vs valve_stuck: fan_failure colapsa power; valve no.
how_to_avoid_false_positives: |
  Cross-check power vs (1·base + ls·180 + 1·900 + occ·8): si en ventana hvac_enable=1
  el residual es ~-900W → consistent with fan_failure.
validation_strategy: |
  state_events durante 4h. Power < 200W con hvac_enable=1 sostenido (modelo aditivo predice >900W).
  Indicador derivado: power_deficit = expected_power - actual_power.
links:
  - PQ-28
  - L-PV-02
  - R-FAULT-03
```

### C-FA-04 — Refrigerant low

```yaml
case_id: C-FA-04
family: physical_faults
fault_family: refrigerant_low
physical_cause: |
  Fuga de refrigerante reduce capacidad frigorífica. T_supply ya no enfría el aire impulsado.
expected_symptoms:
  - |T_supply - T_return| < 1°C (sano: 5-8°C en cooling)
  - T_indoor crece a pesar de hvac_enable=1 mode=cool
  - power normal (compresor sigue funcionando, solo no enfría)
affected_signals: T_supply, T_return (cuando existan)
distinguishing_features: |
  vs fan_failure: power normal vs power colapsado.
  vs valve_stuck: válvula puede responder; lo que no responde es enfriamiento.
how_to_avoid_false_positives: |
  Solo aplicable en modo cool sostenido (>15 min). Excluir transitorios start/stop.
validation_strategy: |
  state_events durante 12h. ΔT_HVAC = |T_supply - T_return|.
  En sano: median(ΔT_HVAC | mode=cool, enable=1) > 5°C.
  En episodio: median < 1°C.
links:
  - PQ-29
  - L-PV-01
  - L-PV-02
  - R-FAULT-04
```

## Familia 7 — Anomalías de dato (transport / quality)

### C-AN-01 — Missing aleatorio

```yaml
case_id: C-AN-01
family: data_anomalies
anomaly_type: random_missing
physical_cause: |
  Pérdida de paquetes red, sensor offline transitorio. Modelo: per-sample probability.
expected_symptoms:
  - N_emitted = (1 - p_missing) · N_expected
  - Distribución uniforme sobre el tiempo
distinguishing_features: |
  vs burst: random missing tiene gaps de 1 sample típicamente; burst tiene gaps consecutivos.
how_to_avoid_false_positives: |
  Diferenciar de gaps por configuración (e.g., outage planificado).
validation_strategy: |
  Comparar count(emitted) vs count(expected) según freq y duración.
  Aceptar si |actual / expected - (1-p_missing)| < 0.005.
links:
  - PQ-31
  - R-AN-01
```

### C-AN-02 — Outliers aleatorios

```yaml
case_id: C-AN-02
family: data_anomalies
anomaly_type: random_outlier
physical_cause: |
  Glitch ADC, EMI puntual. Modelo: per-sample p_outlier, value += N(0, 3·|value|).
expected_symptoms:
  - Quality flag = OUTLIER
  - Magnitud > 3·std normal
  - Punto aislado (no bursts)
distinguishing_features: |
  vs avería sensor: outlier es puntual; sensor avería tiene firma temporal.
how_to_avoid_false_positives: |
  Quality flag debe estar disponible (depende de sink).
validation_strategy: |
  Filtrar quality=OUTLIER. Verificar magnitud y aislamiento.
  Conteo: |N_outliers / N_total - p_outlier| < 0.0005 (con N grande).
links:
  - PQ-32
  - R-AN-02
```

### C-AN-03 — Burst missing

```yaml
case_id: C-AN-03
family: data_anomalies
anomaly_type: burst_missing
physical_cause: |
  Outage red prolongado, reset gateway, mantenimiento.
expected_symptoms:
  - Gap multi-sample (duración en burst_duration_range)
  - Frecuencia controlada por burst_missing_prob_per_day
distinguishing_features: |
  vs random missing: burst es ráfaga.
validation_strategy: |
  RLE sobre presence/absence de samples por timestamp esperado.
  Aceptar si distribución de gaps tiene moda en burst_duration_range.
links:
  - PQ-33
  - R-AN-03
```

### C-AN-04 — Stuck sensor (no implementado)

```yaml
case_id: C-AN-04
family: data_anomalies
anomaly_type: stuck_sensor
physical_cause: |
  ADC congelado, valor último persiste.
expected_symptoms:
  - Valor idéntico durante N samples consecutivos (anormal: con ruido N(0, σ) la igualdad estricta es ~0).
status: NOT_IMPLEMENTED en código actual (L-PV-15).
validation_strategy: |
  Detectar runs de valores idénticos > 5 samples en variables continuas.
  Aceptar caso como "passes — ningún stuck genuino" si runs son < umbral.
links:
  - L-PV-15
  - R-AN-04 (futura)
```

### C-AN-05 — Out-of-order / duplicates / latency (no implementados)

```yaml
case_id: C-AN-05
family: transport_anomalies
status: NOT_IMPLEMENTED (PerturbationsConfig sin caller — L-PV-14).
expected_validation_failures: |
  Cuando se active PerturbationEngine (futuro):
  - duplicates: timestamps con value distinto en mismo ts.
  - out_of_order: ts[i] < ts[i-1] ocasional.
  - latency: jitter alrededor de freq esperado.
links:
  - L-PV-14
```

## Familia 8 — Coherencia general

### C-CO-01 — Esquema canónico

```yaml
case_id: C-CO-01
family: coherence
physical_principle: ninguna (es contractual, no física, pero crítico para validación física).
signals_involved: cualquier output
expected_behavior: |
  100% de DataPoints emitidos cumplen schema canónico CAPTIA.
how_to_validate: scripts/verify_canonical_schema.sh + lint en cada test.
links:
  - PQ-35
  - R-INF-01
```

### C-CO-02 — Reproducibilidad seed

```yaml
case_id: C-CO-02
family: coherence
expected_behavior: |
  Dos runs con mismo seed producen idéntico hash de output.
how_to_validate: |
  Snapshot test ya existe (extensions/bms_calibration/tests/test_determinism.py:24).
  Extender a outputs CSV/Influx.
links:
  - PQ-25
  - R-INF-02
```

### C-CO-03 — Catálogo coverage

```yaml
case_id: C-CO-03
family: coherence
expected_behavior: |
  Variables emitidas == variables.yaml ∪ {variables internas no emitidas}.
how_to_validate: comparison set-based.
notes: |
  relay_1..relay_4 están en catálogo pero NO se generan (L-PV-01 sub-issue).
  Documentar como gap.
links:
  - PQ-37
  - PQ-38
  - L-PV-01
```

## Resumen de cobertura por familia

| Familia | # casos | Implementables hoy | Bloqueados |
|---------|--------|-------------------|------------|
| 1 — Dinámica térmica | 3 | 3 | 0 |
| 2 — Control HVAC | 4 | 4 (C-HV-03 espera FAIL) | 0 |
| 3 — Ocupación / IAQ | 4 | 4 | 0 |
| 4 — Energía | 4 | 4 | 0 |
| 5 — Meteo | 3 | 3 | 0 |
| 6 — Averías físicas | 4 | 0 | 4 (L-PV-01, L-PV-02) |
| 7 — Anomalías dato | 5 | 3 | 2 (no implementado) |
| 8 — Coherencia | 3 | 3 (con caveat catálogo) | 0 |
| **Total** | **30** | **24** | **6** |

El siguiente documento (`04-physical-plausibility-rules.md`) traduce estos casos en reglas concretas con thresholds, ventanas y tolerancias.
