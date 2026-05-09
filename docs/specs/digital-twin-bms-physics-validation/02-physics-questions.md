# 02 — Preguntas físicas que el generador debe superar (Fase 2)

## Contexto

Este documento NO contiene tests ni rangos cerrados. Contiene **preguntas físicas** que el generador BMS debe poder responder afirmativamente con evidencia medible. Las reglas concretas se derivan en `04-physical-plausibility-rules.md` y los experimentos en `05-controlled-simulation-validation.md`.

**Convención**: cada pregunta tiene ID `PQ-NN`, agrupadas por familia. La columna `validation_approach` indica si la respuesta requiere comparación contra literatura, contra otra señal del mismo run, o contra otro run con condiciones controladas.

## Familia A — Dinámica térmica

### PQ-01 — Inercia térmica respetada

```yaml
question: ¿La temperatura interior responde con inercia (no salta) cuando cambia el setpoint?
why_it_matters: |
  Una pared con masa térmica no permite cambios > X °C/min. Saltos artificiales
  delatan modelo no físico.
required_signals:
  - temperature
  - thermostat_setpoint
expected_evidence: |
  ΔT/Δt ≤ 0.5 °C/min en condiciones normales.
  Tras un cambio de setpoint de 5°C, T tarda > 30 min en alcanzar el nuevo valor (con tau=90 min).
possible_failure_modes:
  - HVAC modelado como "teleporte al setpoint" sin alpha.
  - Alpha demasiado alto (dt_min/tau ≥ 0.5).
validation_approach: regla `rate_of_change` + experimento controlado de step de setpoint.
```

### PQ-02 — Drift hacia el exterior con HVAC off

```yaml
question: ¿La temperatura interior tiende al exterior cuando el HVAC está apagado?
required_signals:
  - temperature
  - outdoor_temp
  - hvac_enable
expected_evidence: |
  Durante períodos hvac_enable=0 sostenidos (>2h), la pendiente de T_indoor
  se alinea con el delta (T_indoor - T_outdoor): tiende a cerrar la brecha.
  Correlación T_indoor con T_outdoor durante períodos off > 0.3.
possible_failure_modes:
  - T_indoor permanece constante en setpoint con HVAC off (modelo erróneo).
  - T_indoor diverge sin freno (sin término de coupling).
validation_approach: regla `causal_lag` + experimento con HVAC off forzado.
```

### PQ-03 — Ganancia térmica por ocupación visible

```yaml
question: ¿La temperatura sube perceptiblemente cuando aumenta la ocupación con HVAC off?
required_signals:
  - temperature
  - occupancy
  - hvac_enable
expected_evidence: |
  Con HVAC off y occupancy creciente de 0 a 25 personas en 30 min,
  T sube al menos +0.3°C (con gain=0.02 °C/persona, sumado a alpha bajo).
possible_failure_modes:
  - gain demasiado bajo (no detectable bajo ruido N(0, 0.05)).
  - Modelo desacopla T y occupancy.
validation_approach: regla `correlation` con lag + experimento controlado.
```

### PQ-04 — Estabilización dentro de banda con HVAC enabled

```yaml
question: ¿La T_indoor se estabiliza dentro de ±deadband de setpoint con HVAC enabled?
required_signals:
  - temperature
  - thermostat_setpoint
  - hvac_enable
expected_evidence: |
  Tras 2τ (≈3h) con hvac_enable=1 sostenido, |T - setpoint| ≤ 0.5°C en p95.
possible_failure_modes:
  - Oscilación (overshoot/undershoot) por ausencia de control proporcional.
  - Sesgo permanente (alpha pequeño + ruido alto).
validation_approach: regla `bounded_response`.
```

## Familia B — Control HVAC

### PQ-05 — HVAC se activa cuando hay error térmico significativo

```yaml
question: ¿hvac_enable = 1 cuando |T - setpoint| > umbral?
required_signals:
  - temperature
  - thermostat_setpoint
  - hvac_enable
  - scene_mode
  - occupancy
expected_evidence: |
  En clase ocupada con err > 0.4°C → enable=1 en p99.
  Cualquier escena con err > 1.5°C → enable=1 en p99.
possible_failure_modes:
  - Threshold mismatch (código vs spec).
  - Enable=1 sin error (consumo fantasma).
validation_approach: regla `state_consistency`.
```

### PQ-06 — Modo coherente con T_outdoor

```yaml
question: ¿hvac_mode coincide con la lógica heat/cool/off por T_outdoor?
required_signals:
  - hvac_mode
  - outdoor_temp
expected_evidence: |
  T_outdoor < 16°C → mode == "heat" en >95% de samples.
  T_outdoor > 26°C → mode == "cool" en >95%.
  16 ≤ T_out ≤ 26 → mode ∈ {off, auto}.
possible_failure_modes:
  - Modos invertidos (heat en verano).
  - mode "auto" en condiciones extremas (mal despachado).
validation_approach: regla `state_consistency`.
```

### PQ-07 — Sin short-cycle inverosímil

```yaml
question: ¿Los ciclos de hvac_enable tienen duración > 5 min on y > 5 min off?
required_signals:
  - hvac_enable
expected_evidence: |
  p10 de duración de runs (consecutivos) ≥ 5 min en condiciones estables.
possible_failure_modes:
  - Toggling sample-a-sample alrededor de threshold (L-PV-07).
  - Ausencia de hysteresis.
validation_approach: regla `hysteresis` + métrica `hvac_short_cycle_ratio`.
```

### PQ-08 — Válvula coherente con modo

```yaml
question: ¿heating_valve_pos > 0 implica mode == "heat" y enable == 1?
required_signals:
  - heating_valve_pos
  - hvac_mode
  - hvac_enable
expected_evidence: |
  En todo sample: pos > 0 → mode == "heat" (100% de los casos).
  En cool/off: pos == 0.
possible_failure_modes:
  - Válvula abierta en modo off (cross-talk).
validation_approach: regla `state_consistency`.
```

### PQ-09 — Power refleja activación HVAC

```yaml
question: ¿La potencia eléctrica salta cuando se activa el HVAC?
required_signals:
  - power
  - hvac_enable
expected_evidence: |
  Mediana de power en samples con hvac_enable=1 al menos 700 W mayor que con hvac_enable=0
  (con base ~80W, light variable, occ variable, hvac_full=900W).
possible_failure_modes:
  - Power constante independiente de HVAC.
  - Power sube pero magnitud incorrecta (e.g., +100 W en lugar de +900 W).
validation_approach: regla `coupling` + análisis estadístico.
```

## Familia C — Ocupación y calidad de aire

### PQ-10 — CO₂ aumenta con ocupación

```yaml
question: ¿El CO₂ sube proporcionalmente a la ocupación cuando hay personas?
required_signals:
  - co2
  - occupancy
expected_evidence: |
  Pendiente Δco2/Δt > 0 mientras occupancy > 5 y hvac_enable=0.
  Magnitud: con 20 personas y vent off, ~7.5 ppm/persona/min · 20 = 150 ppm/min instantáneo
  (atenuado por leak).
possible_failure_modes:
  - CO₂ no responde a occupancy.
  - Magnitud demasiado baja (saturación temprana por clipping).
validation_approach: regla `correlation` + experimento de ocupación pulse.
```

### PQ-11 — Ventilación reduce CO₂

```yaml
question: ¿La activación del HVAC reduce CO₂ cuando occupancy es alto?
required_signals:
  - co2
  - hvac_enable
  - occupancy
expected_evidence: |
  En transiciones hvac_enable 0→1 con occupancy estable >10:
  pendiente Δco2/Δt cambia de signo o se reduce significativamente
  (de >+10 ppm/min a <+5 ppm/min en <10 min).
possible_failure_modes:
  - Ventilación no efectiva (vent_k=0).
  - CO₂ ignora hvac_enable.
validation_approach: regla `causal_lag` + experimento controlado.
```

### PQ-12 — CO₂ desciende a outdoor en aulas vacías nocturnas

```yaml
question: ¿El CO₂ regresa a baseline outdoor (~420 ppm) tras 6+ horas con occupancy=0?
required_signals:
  - co2
  - occupancy
expected_evidence: |
  Tras 6h con occupancy=0 sostenido, co2 ≤ outdoor + 30 ppm.
possible_failure_modes:
  - leak_k demasiado bajo (decadencia incompleta).
  - Floor estancado por error de clipping.
validation_approach: regla `bounded_response` + ventana nocturna.
```

### PQ-13 — Transiciones de ocupación no son instantáneas en señales derivadas

```yaml
question: ¿CO₂, ruido y power cambian de forma suavizada (no salto) cuando occupancy cambia abruptamente?
required_signals:
  - co2, noise, power, occupancy
expected_evidence: |
  Aunque occupancy puede cambiar instantáneamente entre samples,
  noise y power debrían cambiar suavemente (<20% por sample con dt=5min).
  CO₂ tiene su propia dinámica y debe responder con τ.
possible_failure_modes:
  - noise salta de 33 a 60 dB en un sample (modelo actual hace esto — ver L-PV-04 modelo 4).
  - power tiene salto coherente (sí, esperado dada arquitectura aditiva).
validation_approach: regla `rate_of_change` por señal.
```

### PQ-14 — Festivos reducen actividad

```yaml
question: ¿Durante vacaciones la occupancy es ~0 y el HVAC standby?
required_signals:
  - occupancy
  - hvac_enable
  - school_mask (derivable de timestamp)
expected_evidence: |
  En fechas en vacation periods (Navidad, Pascua, Verano per ValenciaSchoolCalendar):
  occupancy media diaria ≤ 1.
  hvac_enable_duty ≤ 5%.
possible_failure_modes:
  - Calendario incorrecto (mismatch vendor vs school_calendar — L-PV-06).
  - occupancy>0 en festivos (bug en p_occ).
validation_approach: regla `occupancy_dependency` + experimento día festivo vs lectivo.
```

### PQ-15 — Diferencia día normal vs fin de semana

```yaml
question: ¿Los fines de semana tienen patrones distintos a los días lectivos?
required_signals:
  - occupancy, power, co2 (cualquier señal driven por occupancy)
expected_evidence: |
  Sábado/domingo: occupancy media diaria < 10% del lunes en el mismo mes.
  Power diario: weekend < 30% del weekday.
possible_failure_modes:
  - Igualdad weekend ↔ weekday (calendario ignorado).
validation_approach: regla `seasonality` + comparación agregados diarios.
```

## Familia D — Energía

### PQ-16 — Potencia coherente con estados

```yaml
question: ¿power ≈ 80 + 180·light + 900·hvac + 8·occ + ruido + spikes?
required_signals:
  - power, light_state (interno), hvac_enable, occupancy
expected_evidence: |
  Residuo := power - 80 - 180·ls - 900·he - 8·occ
  E[residuo] ≈ 0, std(residuo) < 200 W (suma de N(0,10) + N(0,20)·ls + N(0,120)·he + N(0,1.5)·occ + spikes).
possible_failure_modes:
  - Coeficientes drift (light_full ≠ 180).
  - Spikes ausentes (raros pero esperados con p=0.0008).
validation_approach: regla `conservation_or_balance` (descomposición lineal).
```

### PQ-17 — Energía es la integral de potencia

```yaml
question: ¿energy[t] ≈ Σ(power · dt)/3.6e6 con error < 1%?
required_signals:
  - power, energy
expected_evidence: |
  En cualquier ventana [t0, t1]:
  |energy[t1] - energy[t0] - cumsum(power[t0:t1])·dt_h/1000| / energy[t1] < 1%.
possible_failure_modes:
  - Reset de counter (no esperado con counter_wire=cumulative_monotonic).
  - Off-by-one en cumsum.
validation_approach: regla `conservation_or_balance`.
```

### PQ-18 — Energy es monotónica creciente

```yaml
question: ¿energy[i] ≥ energy[i-1] siempre?
required_signals: energy
expected_evidence: |
  No hay decrementos. Pendiente derivada > 0 (con power ≥ 0 garantizado por clip).
possible_failure_modes:
  - Power negativa accidental (no debería con clip [0, 6000]).
validation_approach: regla `monotonicity`.
```

### PQ-19 — Consumo bajo en reposo

```yaml
question: ¿En aulas vacías con HVAC off, power se mantiene ≤ 120 W?
required_signals:
  - power, occupancy, hvac_enable, light_state
expected_evidence: |
  Con occupancy=0 AND hvac_enable=0 AND light_state=0:
  power ≤ 80 + 3·std(N(0,10)) + spikes ≈ 110-120 W (sin spikes).
  Con spikes: p99 < 1500 W instantáneo.
possible_failure_modes:
  - base_load drift (consumo fantasma).
validation_approach: regla `bounded_response`.
```

### PQ-20 — Correlación clima ↔ consumo HVAC

```yaml
question: ¿La energía diaria correlaciona con la severidad meteorológica?
required_signals:
  - energy (agregado diario), outdoor_temp (max-min diario o mean)
expected_evidence: |
  Días con T_out_min < 10°C o T_out_max > 30°C: consumo eléctrico diario por aula
  > consumo en días moderados (15 < T_mean < 22) con occupancy similar.
possible_failure_modes:
  - HVAC no se activa con extremos (mode logic mal).
  - Consumo HVAC no escalado por dificultad (modelo es step 900W independiente).
validation_approach: regla `weather_dependency` + análisis por percentiles.
```

## Familia E — Meteo y contexto exterior

### PQ-21 — Temperatura exterior afecta carga térmica

```yaml
question: ¿En invierno la temperatura interior con HVAC off cae por debajo del setpoint con frecuencia?
required_signals:
  - temperature, thermostat_setpoint, outdoor_temp
expected_evidence: |
  En periodos con T_out < 10°C y hvac_enable=0:
  T_indoor < setpoint en >50% de samples (ya sea por sub-aforo o setpoint OOH bajo).
possible_failure_modes:
  - T_indoor desacoplada de T_outdoor (no drift en off).
validation_approach: regla `weather_dependency`.
```

### PQ-22 — Sin saltos artificiales en T_outdoor

```yaml
question: ¿T_outdoor cambia continuamente (sin saltos > 2°C entre samples consecutivos)?
required_signals: outdoor_temp
expected_evidence: |
  |T_out[i] - T_out[i-1]| ≤ 2°C en p99.9 (con dt=5min).
possible_failure_modes:
  - Bug en EWMA noise (alpha mal calibrado).
validation_approach: regla `rate_of_change`.
```

### PQ-23 — Estación afecta patrones

```yaml
question: ¿Las medias mensuales de T_outdoor reflejan la estacionalidad esperada?
required_signals: outdoor_temp
expected_evidence: |
  Julio mean(T_out) ≈ 17 + 9.5·sin(2π(196-200)/365.25) ≈ 26.4°C.
  Enero mean(T_out) ≈ 17 + 9.5·sin(2π(15-200)/365.25) ≈ 7.5°C.
possible_failure_modes:
  - Phase mismatch (peak no en julio).
  - Amplitud incorrecta (Csa Valencia debe ser ~9°C amplitud).
validation_approach: regla `seasonality` + agregado mensual.
```

### PQ-24 — Daylight tiene día/noche

```yaml
question: ¿daylight_lux es 0 antes del amanecer y después del atardecer, peak al mediodía?
required_signals: daylight_lux
expected_evidence: |
  daylight = 0 en hora < sunrise(doy) o > sunset(doy).
  Peak ≈ 700 lux ± 30 alrededor del mediodía solar.
possible_failure_modes:
  - DST mismatch (Europe/Madrid no se ajusta).
  - Peak fuera de mediodía.
validation_approach: regla `seasonality` por día.
```

### PQ-25 — El generador funciona con fixtures deterministas

```yaml
question: ¿Dos runs con mismo seed producen idéntico hash sha256 de la salida?
required_signals: cualquier salida
expected_evidence: |
  hash(run1) == hash(run2) con seed=42, mismo config.
possible_failure_modes:
  - Uso accidental de np.random.seed() (estado global).
  - Ordering no determinista en collections.
validation_approach: regla `reproducibility` (snapshot test).
```

## Familia F — Averías físicas (fault signatures)

### PQ-26 — Sensor drift se detecta como bias creciente

```yaml
question: ¿Durante un evento sensor_drift, el sensor afectado muestra bias respecto a baseline?
required_signals:
  - temperature_supply o temperature (sensor real afectado, según L-PV-01 actualmente solo temperature)
  - temperature de aulas vecinas o de outdoor reference
expected_evidence: |
  Durante un evento sensor_drift de 24h con drift_rate=0.5 °C/día y severity ε[0.3, 1.0]:
  bias acumulado al final ≈ severity · 0.5 °C, detectable comparando contra señal de control.
possible_failure_modes:
  - sensor_drift no aplica drift_rate (L-PV-02: el FaultInjector NO modifica señales actualmente).
  - severity no se aplica a la magnitud.
validation_approach: regla `fault_signature` + experimento marca con control.
notes: |
  Bloqueado por L-PV-02 hasta que se cablee el FaultInjector con un sink de modificación.
```

### PQ-27 — Valve stuck mantiene posición durante el episodio

```yaml
question: ¿Durante un evento valve_stuck, heating_valve_pos no cambia?
required_signals: heating_valve_pos
expected_evidence: |
  Durante el episodio de 60 min, std(heating_valve_pos) ≈ 0.
  Tras el episodio, valve responde de nuevo a temperature - setpoint.
possible_failure_modes:
  - Mismo: bloqueado por L-PV-02.
validation_approach: regla `fault_signature`.
```

### PQ-28 — Fan failure reduce power y rpm

```yaml
question: ¿Durante fan_failure, power consumido cae aunque hvac_enable siga activo?
required_signals: power, hvac_enable, fan_speed_*_state (no existen actualmente — L-PV-01)
expected_evidence: |
  Durante 4h de evento: power ≈ base + occ + light (sin componente HVAC).
  fan_speed_state = 0 (cuando exista la señal).
possible_failure_modes:
  - Bloqueado por L-PV-01 (no hay fan_speed_*_state) y L-PV-02 (no se aplica).
validation_approach: regla `fault_signature`.
```

### PQ-29 — Refrigerant low: T_supply ≈ T_return

```yaml
question: ¿Durante refrigerant_low, temperature_supply y temperature_return convergen?
required_signals: temperature_supply, temperature_return (no existen — L-PV-01)
expected_evidence: |
  Durante 12h: |T_supply - T_return| < 1°C en p95.
  Tras el episodio: diferencia normal restaurada (5-8°C en cooling).
possible_failure_modes:
  - Bloqueado por L-PV-01 (no hay T_supply/T_return) y L-PV-02.
validation_approach: regla `fault_signature`.
```

### PQ-30 — Fault events tienen marca en `state_events`

```yaml
question: ¿Cada FaultEvent generado por FaultInjector aparece como serie en bucket state_events?
required_signals: captia_point_state con variable=fault.<tipo>
expected_evidence: |
  N_eventos generados por FaultInjector == N_series únicas en state_events con variable LIKE 'fault.%'.
possible_failure_modes:
  - Bloqueado por L-PV-02 (FaultEventSink no implementado).
validation_approach: regla `fault_signature` (cobertura).
```

## Familia G — Anomalías de dato (transport/quality)

### PQ-31 — Anomalías de tipo missing reducen volumen

```yaml
question: ¿Con p_missing > 0, el número de DataPoints emitidos es < N_esperado?
required_signals: cualquier salida
expected_evidence: |
  Con p_missing=0.001: N_emitted ≈ 0.999·N_esperado ± 1·std.
possible_failure_modes:
  - p_missing no se aplica (AnomalyEngine bypassed).
validation_approach: regla `anomaly_signature` + count comparison.
```

### PQ-32 — Outliers tienen quality flag

```yaml
question: ¿Los puntos con valor anómalo (p_outlier) tienen quality=OUTLIER?
required_signals: cualquier output con campo quality
expected_evidence: |
  En CSV/JSONL: filas con quality="outlier" tienen value desviado >3σ.
possible_failure_modes:
  - Quality flag no se propaga al sink (depende del format).
validation_approach: regla `anomaly_signature`.
```

### PQ-33 — Burst missing produce gaps multi-punto

```yaml
question: ¿Los burst missing producen huecos consecutivos de duración configurada?
required_signals: cualquier output con timestamps
expected_evidence: |
  Distribución de tamaños de gap muestra al menos un gap > 1·dt en cada día con burst.
  Tamaños caen en burst_duration_range.
possible_failure_modes:
  - Burst no se activa (estado interno bug).
validation_approach: regla `anomaly_signature` + análisis distribución gaps.
```

### PQ-34 — Anomalía de dato ≠ avería física

```yaml
question: ¿Una anomalía de dato (outlier, missing) NO se traduce en cambios de variables correlacionadas?
required_signals: comparar señal afectada vs señales correlacionadas
expected_evidence: |
  Outlier en `temperature` no debe afectar `heating_valve_pos` calculado del MISMO sample
  (porque outlier es post-cálculo). Outlier es una falla de sensor, no del activo.
possible_failure_modes:
  - Outlier se inyecta antes de cálculos (rompe causalidad downstream).
validation_approach: regla `anomaly_signature` + cross-variable check.
```

## Familia H — Coherencia general y reproducibilidad

### PQ-35 — Schema canónico cumplido

```yaml
question: ¿Todos los DataPoints emitidos tienen los 5 tags y measurement correctos?
required_signals: cualquier salida
expected_evidence: |
  scripts/verify_canonical_schema.sh PASS.
  100% de tags presentes en consultas Flux.
possible_failure_modes:
  - Sink omite algún tag.
  - Naming case incorrecto (asset_id no uppercase).
validation_approach: regla `infrastructure` + ContractValidator instanciado.
```

### PQ-36 — Hash determinista con mismo seed

(Duplicado de PQ-25, listado para cobertura por familia.)

### PQ-37 — Variables del catálogo son las generadas

```yaml
question: ¿Las variables emitidas coinciden con `variables.yaml` (sin extras, sin missing)?
required_signals: lista de variables únicas en salida
expected_evidence: |
  set(variables emitidas) == set(variables en variables.yaml) excluyendo light_state (interno).
possible_failure_modes:
  - Variables fantasma (typo en physics).
  - Variables faltantes (relay_1..4 no alimentadas — L-PV-01 sub-issue).
validation_approach: regla `infrastructure` (catalog coverage).
```

### PQ-38 — Sin variables fuera del catálogo

```yaml
question: ¿No se emiten variables que no estén en `variables.yaml`?
required_signals: lista de variables únicas en salida
expected_evidence: |
  set(emitted) ⊆ set(catalog).
possible_failure_modes:
  - Debug variables filtradas a producción.
validation_approach: regla `infrastructure`.
```

### PQ-39 — Frecuencia configurada se respeta

```yaml
question: ¿La frecuencia configurada (5s, 1min, 5min) se respeta en los timestamps?
required_signals: timestamps de cualquier serie
expected_evidence: |
  median(diff(timestamps)) == freq configurado en YAML.
possible_failure_modes:
  - Drift acumulado por float arithmetic.
validation_approach: regla `infrastructure` + análisis distribución dt.
```

### PQ-40 — Horario respetado por timezone

```yaml
question: ¿Las horas locales coinciden con Europe/Madrid (incluyendo DST)?
required_signals: timestamps de cualquier serie + simulation.timezone
expected_evidence: |
  En transición DST (último domingo marzo / octubre):
  los timestamps cubren 23h o 25h respectivamente.
possible_failure_modes:
  - Timezone hardcoded a UTC.
  - DST no respetado.
validation_approach: regla `infrastructure` + experimento de día DST.
```

## Resumen por familia

| Familia | # preguntas | Bloqueadas hoy | Implementables ya |
|---------|------------|---------------|-------------------|
| A — Dinámica térmica | 4 | 0 | 4 |
| B — Control HVAC | 5 | 0 | 5 |
| C — Ocupación / IAQ | 6 | 1 (PQ-14 si calendar mismatch) | 5-6 |
| D — Energía | 5 | 0 | 5 |
| E — Meteo | 5 | 0 | 5 |
| F — Averías físicas | 5 | 5 (todas bloqueadas por L-PV-01/02) | 0 |
| G — Anomalías dato | 4 | 0 | 4 |
| H — Coherencia | 6 | 1 (PQ-37/38 limitadas por L-PV-01) | 4-5 |
| **Total** | **40** | **~6-7** | **~33-34** |

**Conclusión**: la mayoría de la validación física puede implementarse hoy con el código actual. Las preguntas bloqueadas se concentran en averías (todas requieren resolver L-PV-01 catálogo y L-PV-02 wiring). El siguiente documento (`03-physical-cases.md`) agrupa estas preguntas en familias de comportamiento sin escenarios cerrados.
