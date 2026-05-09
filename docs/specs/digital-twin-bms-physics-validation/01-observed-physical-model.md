# 01 — Modelo físico observado (Fase 1)

## Contexto

Documentación, modelo a modelo, de **lo que el código realmente hace** (no lo que la spec aspiracional describe). Cada entrada referencia `file:line`, lista entradas/salidas, ecuación, constantes, límites y validaciones ausentes.

**Notación**:
- *Inputs de contexto*: señales generadas por otros modelos del propio generador.
- *Inputs externos*: configuración (`cfg_*`) o RNG (`rng`).
- *Estado*: variables internas con persistencia entre samples.
- *Outputs*: señales emitidas como variables del catálogo (`variables.yaml`).
- *Constraints*: límites duros del modelo (clip, threshold, etc.).
- *Missing validations*: chequeos que **no se hacen** y deberían.

## Modelo 1 — Temperatura interior

```yaml
model: simulate_indoor_temperature
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/indoor.py
lines: 13-57
purpose: Dinámica térmica primer orden (RC) con HVAC y ganancia por ocupación.
input_signals:
  - outdoor_temp (Series, °C)
  - occupancy (Series, persons)
  - thermostat_setpoint (Series, °C)
  - hvac_enable (Series, 0/1)
input_external:
  - cfg_indoor.tau_minutes (default 90)
  - cfg_indoor.initial_temp (default 20.5)
  - cfg_indoor.occupancy_heat_gain_c_per_person (default 0.02)
  - rng (np.random.Generator)
output_signals:
  - temperature (Series, °C)
state_variables:
  - T[i] (recursivo desde T[i-1] e initial)
equations_or_logic: |
  alpha = dt_min / max(1, tau)
  T[0]  = initial + N(0, 0.4)
  for i in 1..N:
    occ_gain = 0.02 * occupancy[i]
    if hvac_enable[i] == 1:
      target = setpoint[i] + occ_gain
    else:
      target = 0.7 * T[i-1] + 0.3 * outdoor_temp[i] + occ_gain
    T[i] = T[i-1] + alpha * (target - T[i-1]) + N(0, 0.05)
time_constants:
  - tau = 90 min (configurable via cfg_indoor.tau_minutes)
constraints:
  - Sin clip explícito en el cuerpo (variables.yaml range [10, 35] °C aplicado solo si validador instanciado).
physical_limits:
  - Implícitos: target → setpoint cuando HVAC on, target → outdoor cuando HVAC off (con ratio 70/30 en favor del estado previo).
missing_validations:
  - Rate-of-change |T[i]-T[i-1]| ≤ X°C/min (no hay).
  - Sanity: alpha < 1 (válido si dt_min < tau, default cumple).
  - Behavior coherence: T no debe oscilar más de 2°C alrededor de setpoint con HVAC enabled estable.
references:
  - 02-physics-questions.md PQ-01..PQ-04
  - 04-physical-plausibility-rules.md R-T-01..R-T-05
notes:
  - Mezcla 70/30 con T_prev en HVAC off es heurística (no es la formulación canónica RC con outdoor_temp).
  - El parámetro `cfg_indoor.thermal_mass`, `heating_power`, `cooling_effect` que aparece en `config/domains/bms_classrooms/domain.yaml:38-42` NO se lee aquí (ver L-PV-03).
```

## Modelo 2 — CO₂

```yaml
model: simulate_co2
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/indoor.py
lines: 60-99
purpose: Dinámica well-mixed de CO₂ con generación por personas y eliminación por ventilación.
input_signals:
  - occupancy (Series, persons)
  - hvac_enable (Series, 0/1)
input_external:
  - cfg_co2.outdoor_ppm (default 420)
  - cfg_co2.gen_ppm_per_min_per_person (default 7.5)
  - cfg_co2.vent_k_per_min (default 0.06)
  - cfg_co2.leak_k_per_min (default 0.01)
  - rng
output_signals:
  - co2 (Series, ppm)
state_variables:
  - c[i] (recursivo)
equations_or_logic: |
  c[0] = outdoor + N(0, 15)
  for i in 1..N:
    occ = occupancy[i]
    k = leak_k + (vent_k if hvac_enable[i] else 0)
    dc = dt_min * (occ * gen - k * (c[i-1] - outdoor))
    c[i] = c[i-1] + dc + N(0, 3.0)
    c[i] = clip(c[i], outdoor, 2200)
time_constants:
  - tau_vent_on = 1 / (leak_k + vent_k) ≈ 14.3 min
  - tau_vent_off = 1 / leak_k = 100 min
constraints:
  - clip a [outdoor_ppm, 2200] explícito (línea 97).
physical_limits:
  - Asintota (HVAC off, occ constante o): c_inf = outdoor + occ*gen/leak_k
    - Con occ=20, gen=7.5, leak_k=0.01 → c_inf = 420 + 15000 = 15420 ppm (clipeado a 2200)
    - Esto significa que con HVAC off y aforo medio, el CO₂ se satura al límite duro de 2200 ppm en ~30 min.
missing_validations:
  - Anti-coupling: c[i] no debe DECRECER mientras occupancy>0 y hvac_enable=0 sostenido (excepto si c > 2200).
  - Causal_lag: time-to-peak vs ASHRAE expected con gen=4.5 (vs 7.5 actual).
  - Bounded_response: post-noche con occ=0 6h+, c → outdoor ± 5%.
references:
  - 02-physics-questions.md PQ-05..PQ-09
  - 04-physical-plausibility-rules.md R-CO2-01..R-CO2-05
  - L-PV-03 (gen=7.5 vs 02-domain-spec dice 4.5 ASHRAE)
  - L-PV-11 (decadencia lenta con HVAC off)
notes:
  - El parámetro `cfg_co2.base_ppm`, `per_person_ppm`, `decay_rate` de domain.yaml NO se aplica.
  - El generador hace 7.5 ppm/persona/min — si se quiere ASHRAE 4.5, modificar default en código o pasar override por config.
```

## Modelo 3 — Humedad relativa

```yaml
model: simulate_humidity
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/indoor.py
lines: 102-136
purpose: Dinámica RH primer orden con target outdoor + ganancia ocupación.
input_signals:
  - outdoor_temp (Series, °C) — pasada pero NO USADA en el cálculo (firma legacy)
  - occupancy (Series, persons)
input_external:
  - cfg_h.outdoor_mean (default 55)
  - cfg_h.occupancy_gain_per_person (default 0.08)
  - rng
output_signals:
  - humidity (Series, %RH)
state_variables:
  - h[i]
equations_or_logic: |
  alpha = dt_min / 180
  h[0] = outdoor_mean + N(0, 4)
  for i in 1..N:
    target = outdoor_mean + 0.08 * occupancy[i]
    h[i] = h[i-1] + alpha * (target - h[i-1]) + N(0, 0.2)
  h = clip(h, 10, 90)
time_constants:
  - τ = 180 min (hardcoded, no configurable via key)
constraints:
  - clip [10, 90] %RH (línea 136)
physical_limits:
  - Asintota con occ=20: target = 55 + 1.6 = 56.6 %RH
  - Con occ=0: target = 55 (≈ outdoor)
missing_validations:
  - HVAC cooling debería deshumidificar (no modelado — L-PV-09).
  - outdoor_temp influence (no usada — la firma sugiere que debería).
  - Anti-correlation con cooling activo.
references:
  - L-PV-09
  - 04-physical-plausibility-rules.md R-RH-01..R-RH-03
notes:
  - El argumento outdoor_temp se pasa por API legacy pero el body no lo usa.
  - Modelo simplista, conscientemente. Documentar como "v1, conservative".
```

## Modelo 4 — Ruido acústico

```yaml
model: simulate_noise
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/indoor.py
lines: 139-168
purpose: Nivel de ruido base + componente proporcional a ocupación.
input_signals:
  - occupancy (Series, persons)
input_external:
  - cfg_noise.base_unoccupied (default 33)
  - cfg_noise.base_occupied (default 55)
  - cfg_noise.std (default 4)
  - rng
output_signals:
  - noise (Series, dB(A))
equations_or_logic: |
  if occupancy > 0:
    n[i] = base_occupied + 0.35*occupancy + N(0, std)
  else:
    n[i] = base_unoccupied + N(0, std)
  n = clip(n, 25, 90)
constraints:
  - clip [25, 90] dB(A) (línea 168)
physical_limits:
  - Discontinuidad en occupancy=1: salto de 33 a 55+0.35 = 22.35 dB instantáneo.
missing_validations:
  - Smooth transition (no modelada — el salto a 22 dB en un sample es no-físico).
  - Coupling con ventilación (HVAC on añade ruido típicamente, no modelado).
references:
  - 04-physical-plausibility-rules.md R-N-01
notes:
  - El salto instantáneo cuando occupancy cambia de 0 a 1 es una limitación documentada.
```

## Modelo 5 — Iluminancia interior

```yaml
model: simulate_illuminance
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/indoor.py
lines: 171-203
purpose: Lux interior combinando daylight y luz artificial.
input_signals:
  - daylight_lux (Series, lux)
  - light_state (Series, 0/1)
input_external:
  - cfg_light.target_lux_on (default 550)
  - cfg_light.target_lux_off (default 70)
  - cfg_light.std (default 40)
  - rng
output_signals:
  - illuminance (Series, lux)
equations_or_logic: |
  if light_state[i] == 1:
    base[i] = max(daylight_lux[i], 550)
  else:
    base[i] = max(daylight_lux[i], 70)
  lux[i] = base[i] + N(0, 40)
  lux = clip(lux, 0, 2500)
constraints:
  - clip [0, 2500] lux (línea 203)
  - target_off=70 lux con luz off es un piso poco realista (debería ser ~0 con persianas cerradas; refleja "indoor ambient" residual).
physical_limits:
  - Indoor max ≈ 2500 + ruido (≈ 700 daylight + 550 artificial ya saturado por max).
missing_validations:
  - Coherence con daylight_lux (lux interior nunca debe superar daylight + 600 lux).
  - State consistency: light_state=0 con occupancy>0 y daylight<70 → lux ≤ 100 (poco realista; en realidad la gente enciende la luz).
references:
  - 04-physical-plausibility-rules.md R-LX-01..R-LX-02
notes:
  - El uso de max() en lugar de suma es una simplificación (en realidad daylight + artificial se suman aproximadamente).
```

## Modelo 6 — Presencia PIR

```yaml
model: derive_pir_presence
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/indoor.py
lines: 206-226
purpose: Sensor PIR derivado de ocupancia con tasas FP/FN.
input_signals:
  - occupancy (Series, persons)
input_external:
  - rng
output_signals:
  - presence_pir (Series, 0/1)
equations_or_logic: |
  present = occupancy > 0
  fp = U(0,1) < 0.004    (per-sample)
  fn = U(0,1) < 0.01 AND present
  pir = (present OR fp) AND NOT fn
fp_rate: 0.4% per sample
fn_rate: 1.0% per sample (only when truly present)
missing_validations:
  - Latency: PIR real tiene timeout de "no movement detected" típicamente 5-10 min; aquí responde sample a sample.
  - Saturation: PIR no debe parpadear; FP/FN son independientes per-sample → bursts realistas no modelados.
references:
  - 04-physical-plausibility-rules.md R-PIR-01
```

## Modelo 7 — Escena (scene_mode)

```yaml
model: derive_scene
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/actuators.py
lines: 13-56
purpose: Estado de escena {class, out_of_hours, manual} con override raro.
input_signals:
  - occupancy (Series, persons)
  - school_mask (Series, bool)
input_external:
  - rng
output_signals:
  - scene_mode (Series, str enum)
equations_or_logic: |
  base[i] = "class" if (school_mask[i] AND occupancy[i] > 0) else "out_of_hours"
  for i:
    if not in_manual:
      if rng.random() < 0.0008:
        in_manual = true; remaining = U[15, 90)
        scene[i] = "manual"
    else:
      scene[i] = "manual"
      remaining -= 1
      if remaining <= 0: in_manual = false
constraints:
  - p_start manual = 0.0008 per sample (≈1 cada ~1250 samples ≈ 1 vez/aula·día con freq 1 min)
  - duración manual: 15-90 samples
missing_validations:
  - Coherence: scene="class" implica school_mask=true.
  - State transitions: scene="manual" no puede aparecer en t y desaparecer en t+1 (debe respetar duración).
references:
  - 04-physical-plausibility-rules.md R-SC-01
```

## Modelo 8 — Setpoint

```yaml
model: thermostat_setpoint
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/actuators.py
lines: 59-90
purpose: Setpoint según escena con jitter.
input_signals:
  - scene_mode (Series, str)
input_external:
  - cfg_indoor.setpoint_class (default 21.0)
  - cfg_indoor.setpoint_out_of_hours (default 18.0)
  - rng
output_signals:
  - thermostat_setpoint (Series, °C)
equations_or_logic: |
  jitter = N(0, 0.3)
  base[i] = sp_class if scene == "class" else sp_ooh
  if scene[i] == "manual":
    base[i] += N(0, 0.8)
  setpoint[i] = clip(base[i] + jitter, 16, 26)
constraints:
  - clip [16, 26] °C
missing_validations:
  - Setpoint changes no deben superar Δ > 5°C entre samples consecutivos (excepto al cambiar escena).
references:
  - 04-physical-plausibility-rules.md R-SP-01
```

## Modelo 9 — HVAC mode

```yaml
model: hvac_mode
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/actuators.py
lines: 93-118
purpose: Selección de modo {off, heat, cool, auto} por T_outdoor.
input_signals:
  - outdoor_temp (Series, °C)
input_external:
  - rng
output_signals:
  - hvac_mode (Series, str enum {off, heat, cool, auto})
equations_or_logic: |
  mode[t < 16°C] = "heat"
  mode[t > 26°C] = "cool"
  shoulder = 16 ≤ t ≤ 26 → 15% probability "auto", else "off"
constraints: ninguna
missing_validations:
  - Mode no debe oscilar entre heat/cool en ventana corta (no hay deadband alrededor de 16/26).
  - Auto debería ser heat o cool en función del setpoint vs T_indoor (aquí es valor literal "auto").
references:
  - L-PV-08 (sin diferenciación heat/cool en simulate_indoor_temperature)
  - 04-physical-plausibility-rules.md R-HVAC-MODE-01
```

## Modelo 10 — HVAC enable

```yaml
model: hvac_enable
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/actuators.py
lines: 121-146
purpose: Activación del HVAC por umbral de error térmico.
input_signals:
  - temperature (Series, °C)
  - thermostat_setpoint (Series, °C)
  - occupancy (Series, persons)
  - scene_mode (Series, str)
input_external: ninguno
output_signals:
  - hvac_enable (Series, 0/1)
equations_or_logic: |
  err[i] = |temperature[i] - setpoint[i]|
  enable[i] = (
    ((scene == "class") AND (occupancy > 0) AND (err > 0.4)) OR
    (err > 1.5)
  )
thresholds:
  - en clase ocupada: 0.4°C
  - cualquier escena: 1.5°C
missing_validations:
  - Anti short-cycle: ciclos < 5 min (L-PV-07).
  - Hysteresis: el código no usa deadband (turn-on y turn-off al mismo umbral).
  - Coherence: hvac_enable=1 debería tener power > base_load + ε.
references:
  - L-PV-07
  - 04-physical-plausibility-rules.md R-HVAC-EN-01..R-HVAC-EN-03
```

## Modelo 11 — Posición de válvula

```yaml
model: heating_valve_position
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/actuators.py
lines: 149-169
purpose: Apertura proporcional de válvula en modo heat.
input_signals:
  - temperature (Series, °C)
  - thermostat_setpoint (Series, °C)
  - hvac_mode (Series, str)
output_signals:
  - heating_valve_pos (Series, %)
equations_or_logic: |
  err = setpoint - temperature
  pos = clip(err * 35.0, 0, 100) if mode == "heat" else 0
constraints:
  - clip [0, 100] %
  - solo activa si mode == "heat"
missing_validations:
  - State consistency: pos > 0 implica mode == "heat" AND hvac_enable == 1 (la activación de enable no se valida aquí).
  - Rate-of-change: válvula real tiene rate limiter (no abre 0→100% instantáneo).
references:
  - 04-physical-plausibility-rules.md R-VLV-01..R-VLV-02
  - L-PV-08 (no hay cooling_valve_position análoga)
```

## Modelo 12 — Light state

```yaml
model: light_state
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/actuators.py
lines: 172-199
purpose: Encendido de luces basado en ocupación + daylight con extra aleatorio.
input_signals:
  - occupancy (Series, persons)
  - daylight_lux (Series, lux)
input_external: rng
output_signals:
  - light_state (Series, 0/1) — alimenta illuminance y power; NO se emite directamente como variable de catálogo
equations_or_logic: |
  threshold = 250 lux
  base = (occupancy > 0) AND (daylight_lux < 250)
  extra = (occupancy > 0) AND (daylight_lux >= 250) AND (U(0,1) < 0.12)
  light_state = base OR extra
constraints:
  - umbral fijo 250 lux
missing_validations:
  - Light_state debe ser 0 cuando occupancy=0 (excepto vigilancia, no modelada).
  - light_state no debe encender si daylight es muy alto (excepto el 12% extra).
references:
  - 04-physical-plausibility-rules.md R-LS-01
notes:
  - light_state no aparece en variables.yaml — es estado interno.
  - relay_1..relay_4 en variables.yaml NO están alimentados por physics — quedan a 0 si no se overrided.
```

## Modelo 13 — Daylight exterior

```yaml
model: daylight_lux
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/environment.py
lines: 49-79
purpose: Iluminancia ambiente exterior (medida indoor cerca de ventanas).
input_signals: ninguno (puro tiempo)
input_external: ninguno (no configurable)
output_signals:
  - daylight_lux (Series, lux)
equations_or_logic: |
  daylen = 12 + 3·sin(2π(doy - 172)/365.25)  → 9-15 h según estación
  sunrise = 12 - daylen/2
  sunset = 12 + daylen/2
  if hour < sunrise OR hour > sunset:
    lux = 0
  else:
    phase = (hour - sunrise)/(sunset - sunrise)
    lux = 700 · sin(π·phase)^1.2
constraints:
  - peak hardcoded a 700 lux (indoor near windows)
  - sin variación por aula (orientación N/S idéntica)
  - sin cobertura nubosa
missing_validations:
  - Sunset/sunrise consistencia con DST (Europe/Madrid cambia a/de DST en marzo/octubre — el código usa hora local sin ajuste explícito).
references:
  - L-PV-13
  - 04-physical-plausibility-rules.md R-DL-01
```

## Modelo 14 — Temperatura exterior

```yaml
model: outdoor_temperature
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/environment.py
lines: 13-46
purpose: Tª exterior sinusoidal anual + EWMA daily noise.
input_signals: ninguno
input_external:
  - cfg.mean_annual (default 17.0)
  - cfg.amplitude (default 9.5)
  - cfg.daily_noise_std (default 1.0)
  - rng
output_signals:
  - outdoor_temp (Series, °C)
equations_or_logic: |
  doy = index.dayofyear
  seasonal = mean_annual + amplitude·sin(2π(doy - 200)/365.25)  [peak ~late July]
  daily = N(0, noise_std) per sample
  smooth = EWMA(daily, alpha=0.02)
  outdoor_temp = seasonal + smooth
configurable_keys:
  - cfg.outdoor_temp.mean_annual = 17.0  (Csa Valencia)
  - cfg.outdoor_temp.amplitude = 9.5  (Tmax verano ≈ 26.5, Tmin invierno ≈ 7.5)
  - cfg.outdoor_temp.daily_noise_std = 1.0
constraints: ninguna explícita; rango efectivo ≈ [-2.5, +37.5] °C en años extremos.
physical_limits:
  - Sin extremos meteorológicos (olas de calor 40°C+, frentes fríos -5°C no modelados).
  - EWMA alpha=0.02 → constante de tiempo ≈ 50 días (el ruido se suaviza fuertemente).
missing_validations:
  - Realismo estacional: amplitud 9.5°C es razonable para Csa Valencia (referencia AEMET).
  - Continuidad: |T_out[i] - T_out[i-1]| ≤ 0.5°C/min.
references:
  - 04-physical-plausibility-rules.md R-OT-01..R-OT-02
notes:
  - Sin influencia día/noche explícita (solo estacional). En realidad Δdiario ≈ 8-12°C en verano.
  - Esta es una simplificación importante a documentar.
```

## Modelo 15 — Ocupación

```yaml
model: generate_occupancy_count
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/occupancy.py
lines: 39-81
purpose: Series de ocupación por aula vía Poisson sampling.
input_signals:
  - p_occ (Series, [0,1]) — probabilidad de ocupación por timestamp (de schedule)
input_external:
  - capacity (int, sample por aula con N(28,6) clip min 10)
  - util (float, sample por aula con N(0.75,0.10) clip [0.2, 0.98])
  - day_variability (default 0.12)
  - rng
output_signals:
  - occupancy (Series, integer persons)
equations_or_logic: |
  for each unique day d:
    day_mult[d] = clip(N(1.0, 0.12), 0.6, 1.4)
  for i:
    if p_occ[i] <= 0: occ[i] = 0
    else:
      expected = capacity · util · p_occ[i] · day_mult[date_of_i]
      occ[i] = clip(Poisson(max(0.1, expected)), 0, capacity)
constraints:
  - clip [0, capacity]
  - Poisson lambda mínimo 0.1
physical_limits:
  - Una persona puede aparecer/desaparecer entre samples consecutivos (sin lag de entrada/salida).
missing_validations:
  - Smooth transition: ocupación real tiene rampa de entrada (5-10 min al inicio de clase).
  - Coherence con calendar: occupancy debe ser 0 en festivos (verificar via ValenciaSchoolCalendar).
references:
  - 04-physical-plausibility-rules.md R-OCC-01..R-OCC-03
  - L-PV-06 (calendario duplicado)
```

## Modelo 16 — Power

```yaml
model: simulate_power
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/energy.py
lines: 11-49
purpose: Modelo aditivo de potencia activa.
input_signals:
  - occupancy (Series, persons)
  - light_state (Series, 0/1)
  - hvac_enable (Series, 0/1)
input_external:
  - rng (no hay cfg)
output_signals:
  - power (Series, W)
equations_or_logic: |
  base = 80 + N(0, 10)                                 # standby ~80 W
  light = light_state · (180 + N(0, 20))               # ~180 W when on
  hvac = hvac_enable · (900 + N(0, 120))               # ~900 W when on
  occ = occupancy · (8 + N(0, 1.5))                    # ~8 W per person
  spikes = (U(0,1) < 0.0008) · U(500, 1500)            # rare bursts
  power = clip(base + light + hvac + occ + spikes, 0, 6000)
hardcoded:
  - base ≈ 80 W
  - light_full ≈ 180 W
  - hvac_full ≈ 900 W (no diferencia heat/cool)
  - occ_per_person ≈ 8 W (laptops, equipo personal)
  - spike_p = 0.0008, magnitude U(500, 1500) W
constraints:
  - clip [0, 6000] W
physical_limits:
  - Nunca negativa.
  - Saturación a 6000 W (raro con base+light+hvac+occ típico ~ 1300 W).
missing_validations:
  - Coherence: power ≈ base cuando light=0, hvac=0, occ=0.
  - Sum decomposition: power - base - light·180 - hvac·900 - occ·8 ≈ ruido + spikes.
  - Energy balance: power · dt ≈ Δenergy_kWh · 3600·1000 (R-EN-01).
references:
  - 04-physical-plausibility-rules.md R-PW-01..R-PW-03
  - L-PV-08 (sin diferenciación heat/cool en consumo)
```

## Modelo 17 — Energía acumulada

```yaml
model: integrate_energy_kwh
file: vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/energy.py
lines: 52-68
purpose: Integral acumulada de potencia.
input_signals:
  - power (Series, W)
output_signals:
  - energy (Series, kWh, monotonic_cumulative)
equations_or_logic: |
  dt_h = (index[1] - index[0]).total_seconds() / 3600
  energy[i] = cumsum(power[:i+1]) · dt_h / 1000
constraints:
  - Monotónica creciente (porque power ≥ 0).
physical_limits:
  - Crecimiento ≈ 8.7 kWh/día/aula con power medio 365 W.
missing_validations:
  - Monotonicity: energy[i] ≥ energy[i-1] (R-EN-02).
  - Conservation: energy[N] ≈ Σ(power · dt_h)/1000.
  - Counter wrap: si counter_wire=cumulative_monotonic, no debe haber decremento.
references:
  - 04-physical-plausibility-rules.md R-EN-01..R-EN-03
notes:
  - Es métrica derivada — no debe entrar en validación de "rate of change" (siempre crece).
```

## Resumen de constantes físicas observadas

| Magnitud | Constante | Valor | Fuente literatura | Cita |
|----------|-----------|-------|-------------------|------|
| Ganancia térmica por persona | `occupancy_heat_gain_c_per_person` | 0.02 °C/persona | ASHRAE 55: ~75 W/persona sensible; en RC convertido es ≈ 0.01-0.05 °C/persona | indoor.py:40 |
| Tau térmico aula | `tau_minutes` | 90 min | EN ISO 13790: aula media tiene τ = 60-180 min | indoor.py:38 |
| Generación CO₂ por persona | `gen_ppm_per_min_per_person` | 7.5 ppm/persona/min | ASHRAE 62.1: ~4.5 ppm/persona/min (estudiantes nivel actividad bajo) | indoor.py:82 |
| Ventilación HVAC | `vent_k_per_min` | 0.06 /min (τ=16.7 min) | EN 16798 typical 4-6 ACH, traducido a CO₂ removal ≈ 0.05-0.08 /min | indoor.py:83 |
| Leak natural | `leak_k_per_min` | 0.01 /min (τ=100 min) | Edificios modernos: 0.5-1 ACH = 0.008-0.017 /min | indoor.py:84 |
| Tau humedad | hardcoded 180 min | — | Realista | indoor.py:127 |
| Outdoor mean (Valencia Csa) | `mean_annual` | 17 °C | AEMET Valencia 2021-2024: 17.5 °C | environment.py:30 |
| Outdoor amplitude | `amplitude` | 9.5 °C | AEMET Valencia: pico julio 27, mínimo enero 11 → 8 °C amplitud (cercano) | environment.py:31 |
| Power base (standby) | hardcoded 80 W | — | Razonable para aula con un router y stand-by equipos | energy.py:33 |
| Power lighting full | hardcoded 180 W | — | LED panel 4×40W = 160-200 W (consistente) | energy.py:36 |
| Power HVAC full | hardcoded 900 W | — | Split 1.5 HP ≈ 1100 W; aire-aire 1 ton ≈ 1000 W (consistente) | energy.py:39 |
| Power per person | hardcoded 8 W | — | Laptop 50W con 1/6 duty + móvil — algo bajo (esperable 15-25 W) | energy.py:42 |

## Brechas globales del modelo (cross-modelo)

1. **Sin smoothness en ocupación**: la ocupación cambia abruptamente entre samples → CO₂, ruido y power tienen rampas más bruscas que en realidad (`02-physics-questions.md` PQ-13).
2. **Sin diferenciación cooling/heating en `simulate_indoor_temperature`**: tanto heat como cool mueven al setpoint con la misma alpha (L-PV-08).
3. **Sin deshumidificación en cooling**: humidity ignora `hvac_enable` (L-PV-09).
4. **Sin rate limiter en actuadores**: `heating_valve_pos` puede saltar 0→100% en un sample.
5. **Sin coupling power ↔ modo HVAC**: `simulate_power` aplica los mismos 900 W para heat y cool. En realidad cool típicamente consume más (compresor) que heat con bomba de calor.
6. **Sin variación por aula**: ningún parámetro físico se sample por aula (capacity y util sí, pero tau, gen, vent_k son globales).
7. **Sin meteo extrema**: el modelo de outdoor_temperature suaviza tanto que olas de calor no aparecen.

Estas brechas alimentan `02-physics-questions.md` y `04-physical-plausibility-rules.md`.
