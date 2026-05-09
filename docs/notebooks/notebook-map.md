# Mapa de notebooks

> **Última verificación:** 2026-05-10
> **Total:** 45 notebooks didácticos + helpers + mocks.

## 00 Project overview

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `00_arquitectura_medallion_captia.ipynb` | B | ready | Visualización de bronce → plata → oro y mapeo de los 11 casos. |
| `01_schema_captia_influxdb.ipynb` | B | ready | Schema canónico CAPTIA, line protocol, buckets. |
| `02_conexion_influxdb_y_variables_entorno.ipynb` | B | needs-stack | Conexión `.env`, fallback mock. |

## 01 Case A — Pipeline IoT

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `01_explicacion_pipeline_centinela.ipynb` | B | ready | 5 capas CENTINELA+ explicadas. |
| `02_publicacion_mqtt_a_influxdb.ipynb` | I | needs-stack | Publish con `paho-mqtt`. |
| `03_validacion_telegraf_influx_grafana.ipynb` | I | needs-stack | Query Flux + smoke. |

## 02 Case B — Forecast consumo

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `01_eda_consumo_electrico.ipynb` | I | ready | EDA BDG2 mock. |
| `02_bronze_to_silver_energy.ipynb` | I | needs-stack | ETL CSV → CAPTIA. |
| `03_features_forecasting.ipynb` | I | ready | Features lags / rolling. |
| `04_baseline_sarima_xgboost_lstm.ipynb` | A | ready | 3 baselines comparados. |
| `05_validacion_modelo_24h.ipynb` | A | ready | Walk-forward 24h. |

## 03 Case C — Anomalías HVAC

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `01_eda_hvac_fdd.ipynb` | I | ready | LBNL FDD mock con 4 fallos. |
| `02_bronze_to_silver_hvac.ipynb` | I | needs-stack | Etiquetas en `captia_fault_labels`. |
| `03_features_anomalias_hvac.ipynb` | I | ready | ΔT, duty, ratio. |
| `04_isolation_forest_autoencoder.ipynb` | A | ready | IF + AE + ROC. |
| `05_validacion_fallos_etiquetados.ipynb` | A | ready | Recall por tipo. |

## 04 Case D — IAQ + ocupación

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `01_eda_iaq_ocupacion.ipynb` | B | ready | In-Gauge mock. |
| `02_bronze_to_silver_iaq.ipynb` | I | needs-stack | ETL + metadata. |
| `03_features_confort_ocupacion.ipynb` | I | ready | dCO2/dt, IAQ proxy. |
| `04_modelo_ocupacion_desde_ambiente.ipynb` | I | ready | RF + Logistic. |
| `05_validacion_iaq_confort.ipynb` | I | ready | Alertas OMS. |

## 05 Case E — Meteo & solar

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `01_eda_era5.ipynb` | I | ready | ERA5 mock 30 días. |
| `02_bronze_to_silver_weather.ipynb` | I | needs-stack | Conversiones K→°C, J/m²→W/m². |
| `03_features_meteorologicas.ipynb` | I | ready | Dewpoint, daylight. |
| `04_prediccion_solar.ipynb` | I | ready | RF para GHI. |

## 06 Case F — MLOps

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `01_mlflow_lakefs_overview.ipynb` | B | ready | Experiment, run, tag. |
| `02_tracking_experimentos.ipynb` | I | ready | MLflow local SQLite. |
| `03_reproducibilidad_datasets_modelos.ipynb` | I | ready | Hash dataset / modelo. |

## 07 Case G — Calidad con agentes

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `01_reglas_calidad_bronce.ipynb` | I | ready | DSL reglas sobre CSV. |
| `02_reglas_calidad_plata_influxdb.ipynb` | I | needs-stack | Queries Flux. |
| `03_reglas_calidad_oro_ml.ipynb` | I | ready | KL train/test. |
| `04_agentes_especialistas_calidad.ipynb` | A | mocked | 3 agentes mock. |

## 08 Case H — RAG chatbot

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `01_arquitectura_rag_tools.ipynb` | B | ready | Decisión tool vs RAG. |
| `02_tools_influxdb.ipynb` | I | mocked | 3 tools de datos. |
| `03_mock_tools_modelos_predictivos.ipynb` | I | mocked | 3 tools de predicción. |
| `04_rag_documental.ipynb` | I | ready | TF-IDF sobre 12 docs. |
| `05_evaluacion_chatbot.ipynb` | A | ready | Golden set + métricas. |

## 09 Case I — Spark vs Pandas

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `01_bdg2_overview.ipynb` | B | ready | BDG2 estructura y ops. |
| `02_benchmark_pandas.ipynb` | I | ready | Tiempos pandas. |
| `03_benchmark_spark.ipynb` | A | external | Spark / Dask fallback. |
| `04_comparativa_resultados.ipynb` | I | ready | Speedup vs N. |

## 10 Case J — Tráfico YOLO

| Notebook | Nivel | Ejecutable | Resumen |
|---|---|---|---|
| `01_captura_imagenes_dgt.ipynb` | B | ready | Cron + MinIO. |
| `02_inferencia_yolo.ipynb` | A | mocked | Mock YOLO determinista. |
| `03_series_temporales_trafico.ipynb` | I | needs-stack / ready (mock) | ETL conteos a CAPTIA. |
| `04_integracion_meteo_trafico.ipynb` | A | ready | Modelo congestión. |

## Helpers (no notebooks)

- `notebooks/_common/captia_schema.py` — constantes y validador.
- `notebooks/_common/connection.py` — cliente InfluxDB.
- `notebooks/_common/synthetic_mocks.py` — generadores deterministas.
- `notebooks/_common/plotting.py` — estilos comunes.
- `notebooks/_common/template_outline.md` — 18 secciones obligatorias.

## Datos (no notebooks)

- `notebooks/_data/ingauge_aula01_mock.csv` — 1 sem × 1min.
- `notebooks/_data/bdg2_education_subset_mock.csv` — 6 edif × 12m h.
- `notebooks/_data/lbnl_fdd_rtu_mock.csv` — 14 días × 1min con 4 fallos.
- `notebooks/_data/era5_xativa_mock.csv` — 30 días horarios.
- `notebooks/_data/traffic_camera_mock.csv` — 7 días × 15min × 2 cams.
- `notebooks/_data/chatbot_golden_set.csv` — 40 preguntas.
- `notebooks/_data/docs_rag_seed/*.md` — 12 documentos para RAG.
