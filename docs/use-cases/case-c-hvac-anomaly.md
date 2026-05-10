# Caso C — Detección de anomalías en sistemas HVAC

> **Última verificación:** 2026-05-10
> **Audiencia:** equipo G3 (Joan Juan, Edgar, Iván, Joan Benavent).
> **Capa Medallion primaria:** plata + oro.
> **Notebooks:** 5 (`notebooks/03_case_C_hvac_anomaly_detection/`).

## Objetivo

Entrenar modelos no supervisados (Isolation Forest, Autoencoder) capaces de
distinguir funcionamiento HVAC normal de los 4 tipos de fallo definidos en
el catálogo del Caso C: `valve_stuck`, `sensor_drift`, `fan_failure`,
`refrigerant_low`.

## Datos esperados

- **Bronce primario:** LBNL FDD (CSV de 7 subsistemas HVAC) — mock RTU
  reducido en `notebooks/_data/lbnl_fdd_rtu_mock.csv` (14 días × 1 min con
  4 fallos etiquetados).
- **Bronce sintético:** dataset generado vía `caseC_faults.yaml` con
  `BMS_FAULTS_ENABLED=true`.

## Capas Medallion

- **Bronce** — CSV crudo o payload MQTT del generador con fallos activos.
- **Plata** — `captia_point` (variables continuas: `temperature_supply`,
  `temperature_return`, `temperature_outdoor`, `fan_speed_01`).
  `state_events` (señales discretas: `valve_state`, `fan_speed_01_state`).
- **Etiquetas separadas** — `captia_fault_labels` (measurement aparte en
  bucket `state_events`, retención 90 d) — ver
  [variable-catalog](../contracts/variable-catalog.md).
- **Oro** — DataFrame parquet con features + modelos entrenados.

## Schema CAPTIA aplicado

| Tag | Valor |
|---|---|
| `captia_env` | `dev` |
| `domain_id` | `hvac_system` (LBNL) o `bms_classrooms` (IES) |
| `site_id` | `lbnl_building59` o `ies_simarro` |
| `asset_id` | `RTU_01` o `AULAxx` |
| `variable` | `temperature_supply`, `temperature_return`, `valve_*`, `fan_speed_*`, ... |
| **Etiquetas** | tag extra `fault_type` ∈ {`valve_stuck`, `sensor_drift`, `fan_failure`, `refrigerant_low`} |

Las etiquetas no contaminan `captia_point` — viven en `captia_fault_labels`.

## Notebooks asociados

1. `01_eda_hvac_fdd.ipynb` — firmas de cada tipo de fallo.
2. `02_bronze_to_silver_hvac.ipynb` — mapping LBNL → CAPTIA + etiquetas.
3. `03_features_anomalias_hvac.ipynb` — ΔT, duty cycle, ratio fan/valve.
4. `04_isolation_forest_autoencoder.ipynb` — IF + AE + ROC.
5. `05_validacion_fallos_etiquetados.ipynb` — recall por tipo, threshold tuning.

## Modelos y librerías

- **Isolation Forest** (`sklearn.ensemble.IsolationForest`) — anomaly
  score sin etiquetas.
- **Autoencoder MLP** (`sklearn.neural_network.MLPRegressor`) —
  reconstruction error.
- **Validación supervisada** con etiquetas (precision/recall por tipo).

## Validación

- AUC > 0.85 sobre el mock para ambos modelos.
- Recall por tipo > 0.7 (no detector ciego).
- Etiquetas no aparecen en `captia_point`.
- `tests/integration/test_faults.py` confirma 4 tipos cuando
  `BMS_FAULTS_ENABLED=true`.

## Errores comunes

1. **Mezclar etiquetas con telemetría** (cardinalidad explosiva).
2. **Threshold fijo entre runs** — recalibrar con percentil sobre train.
3. **Train sobre todo y eval sobre todo** — contaminación.
4. **Confundir `is_fault` (binario) con `fault_type` (multi-clase)**.

## Reutilización con datos reales

Cuando llegue un ticket de mantenimiento real del IES Simarro, conviértelo a
`captia_fault_labels` con `(start_ts, end_ts, fault_type)`. El detector se
re-entrena mensualmente con los datos del último mes (drift control).

## Coordinación con otros casos

- **Caso H** (G1) consumirá el modelo como tool `check_hvac_anomaly`.
- **Caso F** (G4) versiona el dataset en lakeFS y registra el experimento
  en MLflow.
- **Caso G** (G2/G4) audita el balance de clases y la calidad del
  etiquetado.

## Marco teórico (nivel doctoral)

### Isolation Forest (Liu et al. 2008)

Algoritmo de detección de anomalías basado en aislamiento mediante árboles
binarios construidos por particiones aleatorias. Cada punto $x$ recibe una
puntuación de anomalía:

\[
s(x, n) = 2^{-\frac{E[h(x)]}{c(n)}}
\]

donde:
- $h(x)$ es la profundidad media del path al aislar $x$ en un árbol.
- $E[h(x)]$ es la esperanza sobre el ensemble de árboles.
- $c(n) = 2 H(n-1) - 2(n-1)/n$ con $H(i)$ harmonic number.
- $s(x) \to 1$ indica anomalía; $s(x) \to 0.5$ indica normal.

Hiper-parámetros calibrados:
- `n_estimators = 100`.
- `max_samples = 256`.
- `contamination` = $\sim 0.02$ (fracción esperada de fallos en BMS, según LBNL FDD).

### Autoencoder (Hinton & Salakhutdinov 2006)

Red neuronal que aprende una función de identidad a través de un cuello de
botella:

\[
\hat{x} = D(E(x)), \quad E: \mathbb{R}^d \to \mathbb{R}^k, \quad D: \mathbb{R}^k \to \mathbb{R}^d, \quad k \ll d
\]

con $k = 8$ neuronas en el bottleneck para $d = 24$ features (lags + meteo + horarios).

La señal de anomalía es el error de reconstrucción:

\[
e(x) = \| x - \hat{x} \|_2^2
\]

con umbral $\theta = \mu_e + 3 \sigma_e$ calculado sobre el conjunto de
entrenamiento (puro normal, sin fallos).

### Modelo de fallos HVAC (ADR-010)

Los 4 tipos de fallo simulados con sus signature observables:

| Tipo | Variable afectada | Signature | Duración típica |
|---|---|---|---|
| `sensor_drift` | `temperature_01` | drift lineal $+0.5$ °C/h | $\sim 60$ min |
| `valve_stuck` | `valve_state`, `temperature_01` | $\Delta T \to 0$ tras setpoint change | $\sim 60$ min |
| `fan_failure` | `fan_speed_01_state`, `temperature_supply` | $\dot V \to 0$, $T_{supply}$ converge a $T_{coil}$ | $\sim 240$ min |
| `refrigerant_low` | `temperature_supply` − `temperature_return` | $\Delta T_{cool}$ cae $50 \%$ | $\sim 12$ h |

### Métricas de evaluación

\[
\begin{aligned}
\text{Precision} &= \frac{TP}{TP + FP} \\
\text{Recall} &= \frac{TP}{TP + FN} \\
\text{F1} &= 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}} \\
\text{TPR}@1\%FPR &= \text{Recall sujeto a FPR} \leq 0.01
\end{aligned}
\]

Objetivos: $\text{F1} \geq 0.85$ por tipo de fallo, $\text{TPR}@1\%\text{FPR} \geq 0.7$.

## ROI del Caso C

| Concepto | Valor anual |
|---|---|
| Detección temprana evita avería catastrófica | $\sim$ 2 incidentes/año × 3 500 € |
| Reducción downtime aulas (2 h × 200 días lectivos) | $\sim$ 800 € productividad |
| **Beneficio bruto** | **+7 800 €/año** |
| Coste integración Caso C en operaciones | -2 000 € one-time |
| **Payback** | **~3 meses** |

## Bibliografía

- Liu, F., Ting, K., Zhou, Z. (2008). *Isolation Forest*. ICDM 2008.
- Hinton, G., Salakhutdinov, R. (2006). *Reducing dimensionality with NN*. Science.
- LBNL FDD Dataset — [datadryad.org/stash/dataset/doi:10.7941/D1N33Q](https://datadryad.org/stash/dataset/doi:10.7941/D1N33Q).
- ASHRAE Guideline 36-2021 — High-Performance Sequences of Operation for HVAC.
