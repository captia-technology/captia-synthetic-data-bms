# Caso B — Predicción de consumo eléctrico a 24h

> **Última verificación:** 2026-05-10
> **Audiencia:** equipo G1 (Sergio, Ainhoa, Guillermo, Jordi).
> **Capa Medallion primaria:** oro (features ML + modelo).
> **Notebooks:** 5 (`notebooks/02_case_B_energy_forecasting/`).

## Objetivo

Entrenar modelos SARIMA / XGBoost / LSTM para predecir `power_01` con
horizonte de 24 h. El modelo debe ser directamente reutilizable cuando
CAPTIA proporcione el dump de InfluxDB con datos del IES Simarro o cuando
los sensores reales generen suficiente histórico.

## Datos esperados

- **Bronce primario:** subset BDG2 educacional (5–10 edificios × 12 meses
  horarios) — mock determinista en
  `notebooks/_data/bdg2_education_subset_mock.csv`.
- **Bronce alternativo:** UCI Appliances Energy.
- **Coordinar con G2** (Caso I) para que el subset venga de allí cuando
  esté procesado.

## Capas Medallion

| Capa | Contenido | Bucket / fichero |
|---|---|---|
| Bronce | `electricity.csv`, `weather.csv` | lakeFS o filesystem |
| Plata | `captia_point` con `power_01`, `temperature_outdoor`, `solar_irradiance` | `telemetry` (raw 14d), rollups `_1h` |
| Oro | DataFrame parquet con features + modelo entrenado | `output/case_B/` |

## Schema CAPTIA aplicado

| Tag | Valor |
|---|---|
| `captia_env` | `dev` |
| `domain_id` | `bms_buildings` (BDG2) o `bms_classrooms` (IES Simarro) |
| `site_id` | `bdg2_education` o `ies_simarro` |
| `asset_id` | `bdg2_bldg_XX` o `AULAxx` |
| `variable` | `power_01`, `temperature_outdoor`, `solar_irradiance`, `occupancy` |

## Notebooks asociados

1. `01_eda_consumo_electrico.ipynb` — patrones diario / semanal / vacaciones.
2. `02_bronze_to_silver_energy.ipynb` — ETL CSV → InfluxDB.
3. `03_features_forecasting.ipynb` — lags 24h/168h, rolling, codificación cíclica.
4. `04_baseline_sarima_xgboost_lstm.ipynb` — 3 modelos comparados con MAE/MAPE/RMSE.
5. `05_validacion_modelo_24h.ipynb` — walk-forward y métricas por horizonte.

## Modelos y librerías

- **SARIMA**: `statsmodels` — punto de referencia clásico.
- **XGBoost**: `xgboost` o `RandomForestRegressor` (fallback) — mejor en
  regímenes con features exógenas.
- **LSTM**: opcional con TensorFlow / PyTorch.

## Validación

- MAE 24 h debe ser < 2× MAE 1 h en el mock.
- El modelo debe **batir** la línea naive (mismo valor 24 h atrás).
- Sin leakage temporal: `TimeSeriesSplit` con shuffle desactivado.

## Errores comunes

1. **Random split** (`train_test_split` con shuffle): rompe la temporalidad.
2. **Codificar `dow` como entero**: lunes y domingo aparecerán muy lejos.
3. **`rolling().mean()` sin shift(1)**: leakage del valor actual.
4. **MAPE con consumo 0**: usar `MAE` o `sMAPE`.

## Reutilización con datos reales

`make_features(df)` es pura: misma firma para BDG2 mock, BDG2 completo o
`simarro-prod`. Solo cambia la fuente de datos.

## Coordinación con otros casos

- **Caso E** (G3) entrega `temperature_outdoor` y `solar_irradiance` en
  InfluxDB — features exógenas críticas.
- **Caso H** (G1) consumirá el modelo como tool `get_consumption_prediction`.
- **Caso F** (G4) define la convención de naming de experimentos MLflow.

## Marco teórico (nivel doctoral)

### Modelos SARIMA

El modelo $\text{SARIMA}(p, d, q)(P, D, Q)_s$ con período estacional $s$ se define como:

\[
\Phi_P(B^s) \phi_p(B) (1 - B)^d (1 - B^s)^D y_t = \Theta_Q(B^s) \theta_q(B) \varepsilon_t
\]

donde $B$ es el operador de retardo, $y_t$ la serie observada (consumo
eléctrico horario `power_01`), y $\varepsilon_t \sim \mathcal{N}(0, \sigma^2)$.

Para Simarro elegimos $s = 24$ (estacionalidad diaria) y $(p,d,q)(P,D,Q)_{24} =
(2,0,2)(1,1,1)_{24}$ tras minimizar AIC en el dataset BDG2.

### XGBoost para series temporales

Para $\hat{y}_t$ usamos un modelo de boosting con gradiente:

\[
\hat{y}_t = \sum_{k=1}^{K} f_k(\mathbf{x}_t), \quad f_k \in \mathcal{F}
\]

donde $\mathbf{x}_t = [y_{t-1}, y_{t-24}, \text{hour}, \text{dow}, T_{out}, ...]$
es el vector de features lags + calendario + meteorología.

La función objetivo regularizada:

\[
\mathcal{L}(\phi) = \sum_t \ell(y_t, \hat{y}_t) + \sum_k \Omega(f_k), \quad
\Omega(f) = \gamma T + \frac{1}{2} \lambda \|w\|^2
\]

con $T$ = número de hojas y $w$ los pesos.

### LSTM (Long Short-Term Memory)

La celda LSTM mantiene estado interno $c_t$ y $h_t$:

\[
\begin{aligned}
f_t &= \sigma(W_f [h_{t-1}, x_t] + b_f) \\
i_t &= \sigma(W_i [h_{t-1}, x_t] + b_i) \\
\tilde{c}_t &= \tanh(W_c [h_{t-1}, x_t] + b_c) \\
c_t &= f_t \odot c_{t-1} + i_t \odot \tilde{c}_t \\
o_t &= \sigma(W_o [h_{t-1}, x_t] + b_o) \\
h_t &= o_t \odot \tanh(c_t)
\end{aligned}
\]

donde $\sigma$ es la sigmoide, $\odot$ producto Hadamard, y los $f_t, i_t, o_t$
son los gates forget, input y output.

### Métricas de evaluación

\[
\begin{aligned}
\text{MAE} &= \frac{1}{n} \sum_{t=1}^{n} | y_t - \hat{y}_t | \\
\text{RMSE} &= \sqrt{\frac{1}{n} \sum_{t=1}^{n} (y_t - \hat{y}_t)^2} \\
\text{sMAPE} &= \frac{100\%}{n} \sum_{t=1}^{n} \frac{|y_t - \hat{y}_t|}{(|y_t| + |\hat{y}_t|)/2}
\end{aligned}
\]

Objetivos para Simarro: $\text{MAE} \leq 0.15$ kWh, $\text{sMAPE} \leq 12\%$.

## ROI estimado del Caso B

| Métrica | Valor |
|---|---|
| Ahorro consumo HVAC tras forecast + ajuste setpoint | $\sim 15 \%$ |
| Aulas tipo Simarro (40) | 9 600 kWh / aula·año |
| Coste energía España 2025 | 0.14 €/kWh |
| **Ahorro centro**: $40 \cdot 9\,600 \cdot 0.14 \cdot 0.15$ | **8 064 €/año** |
| Coste implantación + integración | ~3 000 € one-time |
| **Payback** | **~ 5 meses** |

## Bibliografía

- Box, G., Jenkins, G., Reinsel, G. (2015). *Time Series Analysis*. Wiley.
- Chen, T., Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System*. KDD '16.
- Hochreiter, S., Schmidhuber, J. (1997). *Long Short-Term Memory*. Neural Computation.
- BDG2 — Building Data Genome 2 ([github.com/buds-lab/building-data-genome-project-2](https://github.com/buds-lab/building-data-genome-project-2)).
- ASHRAE 90.1-2022 — Energy Standard for Buildings.
