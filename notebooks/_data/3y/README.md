# Datasets 3 años — versiones extendidas para ML serio

Esta subcarpeta contiene **versiones de 3 años** de los mocks didácticos
de `notebooks/_data/`, con **enriquecimiento de columnas** y compresión
gzip para tamaño manejable en repo.

> Generación: `uv run python scripts/build_3year_datasets.py`
> Determinismo: `seed=42` bit-a-bit reproducible.
> Formato: `*.csv.gz` (gzip nivel 9).

## Inventario

| Fichero | Periodo | Granularidad | Filas | Tamaño | Caso ML |
|---|---|---|---|---|---|
| `bdg2_education_subset_3y.csv.gz` | 2024-01-01 → 2026-12-15 | horaria | 155 520 | 1.7 MB | B (forecast), I (Big Data) |
| `era5_xativa_3y.csv.gz` | 2024-06-01 → 2027-05-31 | horaria | 26 280 | 0.45 MB | E (meteo + solar) |
| `ingauge_aula01_3y.csv.gz` | 2024-09-09 → 2027-09-08 | 5 min | 315 360 | 5.1 MB | A (pipeline), D (IAQ) |
| `lbnl_fdd_rtu_3y.csv.gz` | 2024-06-01 → 2027-05-31 | 5 min | 315 360 | 2.3 MB | C (anomalías HVAC) |
| `traffic_camera_3y.csv.gz` | 2024-09-01 → 2027-08-31 | 15 min | 210 240 | 1.3 MB | J (tráfico DGT) |
| **`bms_simarro_canonical_12m.csv.gz`** ⭐ | 2025-09-01 → 2026-03-22 | 5 min, 10 aulas | **2 997 955** | **15 MB** | **TODOS los casos — schema canónico CAPTIA** |
| **Total** | | | **~4 M filas** | **~26 MB** | |

> ⭐ **`bms_simarro_canonical_12m.csv.gz`** es la salida real del **generador
> hexagonal vendoreado del repo** ejecutado contra `bms_v1_caseB_consumption.yaml`.
> Schema canónico CAPTIA estricto: 12 columnas (`timestamp, domain_id, site_id,
> asset_id, variable, value, unit, data_type, point_type, quality, origin, pvn`),
> 22 variables × 10 aulas × 5 min granularity = 3 M puntos. Idéntico bit-a-bit
> al que produce el stack en producción (mismo seed=42, mismas físicas).

## Por qué 3 años

| Modelo / técnica | Histórico mínimo | Razón |
|---|---|---|
| SARIMA estacional anual | 2 años | Capturar estacionalidad anual completa con varianza |
| LSTM / Transformer | 2-3 años | Suficientes ciclos para validation rolling |
| Detección anomalías HVAC | 6-12 meses | Cubrir verano + invierno con sus modos opuestos |
| Calibración energética | 12 meses | Comparable con factura anual |
| Benchmark Big Data Spark | ≥ 1 M filas | Salir del rango pandas-friendly |

## Columnas enriquecidas vs. mocks 1 año originales

### `bdg2_education_subset_3y.csv.gz` (12 columnas)

Originales: `timestamp, building_id, power_kw, t_outdoor, ghi`.
**Añadidas**: `year, month, dow, hour, is_weekend, is_school_hours, season`
(útiles para feature engineering en Caso B).

### `era5_xativa_3y.csv.gz` (11 columnas)

Originales: `timestamp, t_air_c, ghi_w_m2, wind_speed_ms, precip_mm, pressure_hpa`.
**Añadidas**: `day_of_year, hour, dew_point_c` (Magnus approximation),
`relative_humidity, solar_zenith_deg` (calculado para latitud 38.99°N Xátiva).

### `ingauge_aula01_3y.csv.gz` (12 columnas)

Originales: `timestamp, Indoor_CO2, Indoor_Temp, Indoor_Hum, Indoor_Noise,
Indoor_Lux, Occupied, People_Count, CoolingState`.
**Añadidas**: `iaq_index` (mapeo CO₂ → 0-500 EPA-like), `comfort_pmv`
(Fanger 1970 simplificado, met=1.2 clo=0.5), `power_w` (proxy aditivo).

### `lbnl_fdd_rtu_3y.csv.gz`

Mismas columnas que original más `fault_label` y `fault_severity` siempre presentes.

### `traffic_camera_3y.csv.gz`

Originales: `timestamp, camera_id, vehicles, weather_flag`.
**Añadidas**: `cars, trucks, motorbikes, bicycles` (decomposición tipo
COCO weights), `congestion_level` (`fluid` / `slow` / `dense` / `congested`).

### `bms_simarro_canonical_12m.csv.gz` ⭐ (12 columnas, schema canónico CAPTIA)

Producido directamente por el generador hexagonal `vendor/synthetic-generator/`
(no por los mocks de `notebooks/_common/synthetic_mocks.py`). Schema:

| Columna | Tipo | Significado |
|---|---|---|
| `timestamp` | ISO 8601 con TZ | Hora del muestreo (Europe/Madrid) |
| `domain_id` | string | `bms_classrooms` (canónico CAPTIA) |
| `site_id` | string | `ies_simarro` (canónico CAPTIA) |
| `asset_id` | string | `AULA01..AULA10` |
| `variable` | string | `temperature_01`, `co2`, `relative-humidity`, ... 22 variables |
| `value` | float | Valor del field canónico |
| `unit` | string | `°C`, `ppm`, `%`, `W`, etc. |
| `data_type` | string | `float`, `boolean`, `int` |
| `point_type` | string | `sensor`, `actuator`, `derived` |
| `quality` | string | `OK`, `BAD`, `STALE` |
| `origin` | string | `synthetic` (este repo) o `simarro-prod` (real) |
| `pvn` | string | Process Variable Name = `${asset_id}__${variable}` |

Equivalente directo al schema InfluxDB `captia_point` (los 5 tags
[`captia_env`, `domain_id`, `site_id`, `asset_id`, `variable`] + field
`value`). El `captia_env` se aplica en sink (default `dev`).

Cómo se generó:

```bash
make demo                                                                    # arrancar infra
curl -X POST http://localhost:8121/v1/datasets/export                        \
     -H "Authorization: Bearer $BMS_API_TOKEN"                               \
     -H "Content-Type: application/json"                                     \
     -d '{"config_path":"/app/config/projects/bms_v1_caseB_consumption.yaml",\
          "format":"csv_long","months":12,"include_faults":false}'
# → /app/output/ies_simarro_12m_*.csv (380 MB sin comprimir)
docker cp captia-bms-generator:/app/output/ies_simarro_12m_*.csv ./output/
gzip -9 output/ies_simarro_12m_*.csv
```

Compresión: 380 MB → 15 MB (ratio 25×, típico CSV con tags repetitivos).

## Cómo se generan

```bash
# Local (sin stack):
uv run python scripts/build_3year_datasets.py

# Con export del generador BMS canónico (requiere stack vivo + .env):
uv run python scripts/build_3year_datasets.py --include-bms
```

Re-ejecuciones producen ficheros idénticos byte-a-byte (`seed=42`).

## Cómo cargar en notebooks

```python
import pandas as pd

# Por defecto pandas detecta el .gz por la extensión
df = pd.read_csv(
    "../_data/3y/ingauge_aula01_3y.csv.gz",
    comment="#",         # ignora el header MOCK
    parse_dates=["timestamp"],
)
print(df.shape, df.columns.tolist())
```

Para Caso I (Spark vs Pandas) un truco útil:

```python
# Spark lee gzip directamente
spark.read.option("header", "true").csv("file:///path/to/3y/*.csv.gz")
```

## Datasets reales vs mocks

Los mocks de esta carpeta son **sintéticos didácticos** — no reemplazan
los datasets reales en producción. Para entrenamiento serio, solicita
acceso a los datos reales (BDG2 completo 53M filas, ERA5 Copernicus,
LBNL FDD official, In-Gauge dataset original, DGT cámaras) cuyos
enlaces están en `docs/use-cases/` y `docs/captia-corporate/about.md`.

## Generación con el generador BMS canónico

Para obtener un dataset 3 años producido por el generador hexagonal
del repo (con schema canónico CAPTIA `captia_point` + 5 tags + field
`value`), levantar el stack y ejecutar:

```bash
make demo                                                             # arrancar infra
curl -X POST http://localhost:8120/v1/datasets/export \
     -H "Authorization: Bearer $BMS_API_TOKEN"                        \
     -H "Content-Type: application/json"                              \
     -d '{"config_path": "/app/config/projects/bms_v1_3years.yaml",    \
          "format": "line_protocol",                                  \
          "months": 36}'
# → output/bms_simarro_3years.lp (~600-900 MB comprimido)
```

El escenario completo: [`config/projects/bms_v1_3years.yaml`](https://github.com/captia-technology/captia-synthetic-data-bms/blob/main/config/projects/bms_v1_3years.yaml).

> **CAPTIA Technology** — datos sintéticos rigurosos para inteligencia
> artificial aplicada a edificación inteligente, energía industrial y
> educación técnica.
