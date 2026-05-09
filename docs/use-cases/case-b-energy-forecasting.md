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
