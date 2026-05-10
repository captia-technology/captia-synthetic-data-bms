# Caso E — Meteorología y predicción de generación solar

> **Última verificación:** 2026-05-10
> **Audiencia:** equipo G3.
> **Capa Medallion primaria:** bronce → oro.
> **Notebooks:** 4 (`notebooks/05_case_E_weather_solar/`).

## Objetivo

Procesar ERA5 (ECMWF) para Xàtiva, ingestarlo en InfluxDB con
`domain_id=weather_station` y entrenar un predictor de irradiancia / FV.
Los datos servirán de input al Caso B y al Caso H.

## Datos esperados

- **Bronce primario:** ERA5 NetCDF (ECMWF Climate Data Store API) — mock
  30 días horarios en `notebooks/_data/era5_xativa_mock.csv`.
- **Bronce alternativo:** AEMET API JSON.

## Capas Medallion

| Capa | Contenido | Bucket |
|---|---|---|
| Bronce | NetCDF ERA5 / CSV AEMET | filesystem |
| Plata | `captia_point` con `temperature_outdoor`, `solar_irradiance`, `wind_speed`, `precipitation`, `pressure` | `telemetry` |
| Oro | Modelo predicción solar + tool de chatbot | `output/case_E/` |

## Schema CAPTIA aplicado

| Tag | Valor |
|---|---|
| `captia_env` | `dev` |
| `domain_id` | `weather_station` |
| `site_id` | `xativa` |
| `asset_id` | `era5_gridpoint` |
| `variable` | `temperature_outdoor`, `solar_irradiance`, `wind_speed`, `precipitation`, `pressure`, `dewpoint` |

## Notebooks asociados

1. `01_eda_era5.ipynb` — mock 30 días, diurnal cycle.
2. `02_bronze_to_silver_weather.ipynb` — conversiones K→°C, J/m²→W/m², m→mm.
3. `03_features_meteorologicas.ipynb` — dewpoint Magnus, daylight flag.
4. `04_prediccion_solar.ipynb` — RandomForest GHI con T + hora + DOY.

## Conversiones unitarias

| Variable ERA5 | Conversión | CAPTIA |
|---|---|---|
| `2m_temperature` (K) | `K - 273.15` | `temperature_outdoor` (°C) |
| `surface_solar_radiation_downwards` (J/m²) | `/ 3600` | `solar_irradiance` (W/m²) |
| `total_precipitation` (m) | `× 1000` | `precipitation` (mm) |
| componente viento u/v (m/s) | `sqrt(u²+v²)` | `wind_speed` (m/s) |
| `surface_pressure` (Pa) | `/ 100` | `pressure` (hPa) |

## Validación

- RMSE GHI < 250 W/m² sobre el mock.
- Rango físico respetado: `solar_irradiance ∈ [0, 1100]`,
  `temperature_outdoor ∈ [-5, 45]`, etc.
- Dewpoint ≤ T_air siempre.

## Errores comunes

1. **Confundir GHI con DNI** (Direct Normal Irradiance).
2. **No restar 273.15** cuando ERA5 entrega K.
3. **Usar `precip_mm` como tasa**: en realidad es acumulada por hora.
4. **Vector vs escalar para viento**: promediar componentes, no magnitud.

## Reutilización con datos reales

Para descargar ERA5 real:

```bash
pip install cdsapi
# Configurar ~/.cdsapirc con UID y key
python scripts/era5_download.py --start 2024-01 --end 2024-12 --area "Xativa"
```

El notebook `02_bronze_to_silver_weather.ipynb` lee NetCDF con `xarray.open_dataset`
en lugar del CSV mock.

## Coordinación con otros casos

- **Caso B** (G1) — `temperature_outdoor` y `solar_irradiance` son features
  críticas. Coordinar la descarga.
- **Caso H** (G1) — el modelo se sirve como tool `get_weather_prediction`.
- **Caso J** (G5) — meteorología cruzada con tráfico (lluvia → congestión).

## Marco teórico (nivel doctoral)

### Modelo de irradiancia solar

\[
G_h(t) = G_b(t) + G_d(t), \quad G_b(t) = G_{sc} \cdot \tau_b(t) \cdot \cos\theta_z(t)
\]

con $G_{sc} = 1361$ W/m², $\theta_z$ ángulo cenital del sol calculado a partir
de declinación $\delta$, latitud $\phi$ (Xátiva 38.99°N) y ángulo horario $\omega$:

\[
\cos\theta_z = \sin\delta \sin\phi + \cos\delta \cos\phi \cos\omega
\]

### Predicción solar XGBoost

\[
\hat{G}_h(t) = \text{XGB}(\mathbf{x}_t) \cdot G_{clearsky}(t)
\]

separando astronomía (determinista) de meteorología (estocástica via clear-sky index).

### Métricas

\[
\text{Skill} = 1 - \frac{\text{RMSE}_{model}}{\text{RMSE}_{persistence}}
\]

Objetivos: $\text{nMAE} \leq 8\%$ a 24 h, $\text{Skill} \geq 0.3$.

## ROI Caso E

Optimización despacho solar (centro 50 kWp): **+800 €/año**. Sinergia con
Caso B forecast: **+500 €/año**. Coste integración ERA5+AEMET: 1 200 €
one-time. **Payback ~12 meses**.

## Bibliografía

- ERA5 Copernicus — [cds.climate.copernicus.eu](https://cds.climate.copernicus.eu).
- Iqbal, M. (1983). *An Introduction to Solar Radiation*. Academic Press.
- AEMET Open Data — [opendata.aemet.es](https://opendata.aemet.es).
- pvlib python — [pvlib-python.readthedocs.io](https://pvlib-python.readthedocs.io).