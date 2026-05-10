# 00 — Inventario completo de notebooks

> **Última verificación:** 2026-05-10  
> **Generado por:** `scripts/audit_notebooks.py --inventory`  
> **Total notebooks:** 45 (3 overview + 42 casos A..J).

Esta tabla cataloga los 45 notebooks didácticos del repo con 18 columnas
de metadatos extraídos del JSON nbformat 4. Es la base de la auditoría:
todas las matrices y reviews dependen de esta vista.

| # | Ruta | Caso | Etapa | Título | Capa Medallion | Datasets | Helpers `_common` | md / code | Sec | Outputs % | Mocks | Sin secretos | Sin paths abs | Cita schema | Assert | Score | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `notebooks/00_project_overview/00_arquitectura_medallion_captia.ipynb` | Transversal | 00 | Arquitectura Medallion aplicada a CAPTIA Synt… | transversal | BDG2 educational (público resampled), DGT cameras (sintético), ERA5 Xàtiva (público mockeado), Golden set chatbot (sintético), LBNL FDD RTU (público mockeado) | captia_schema, connection, plotting, synthetic_mocks | 23/7 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.6** | OK |
| 2 | `notebooks/00_project_overview/01_schema_captia_influxdb.ipynb` | Transversal | 01 | Schema canónico CAPTIA en InfluxDB — measurem… | plata | ERA5 Xàtiva (público mockeado) | captia_schema, connection, plotting, synthetic_mocks | 23/7 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.4** | OK |
| 3 | `notebooks/00_project_overview/02_conexion_influxdb_y_variables_entorno.ipynb` | Transversal | 02 | Conexión a InfluxDB con variables de entorno … | transversal | ERA5 Xàtiva (público mockeado) | captia_schema, connection, plotting, synthetic_mocks | 23/5 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 4 | `notebooks/01_case_A_pipeline_iot/01_explicacion_pipeline_centinela.ipynb` | Pipeline IoT | 01 | Pipeline IoT CENTINELA+ — explicación de las … | bronce → plata | — | captia_schema, connection, plotting, synthetic_mocks | 23/7 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **7.9** | OK |
| 5 | `notebooks/01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb` | Pipeline IoT | 02 | Publicación MQTT a InfluxDB — del CSV al brok… | bronce → plata | In-Gauge AULA01 (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/8 | 22 | 100.0% | ✓ | ✓ | ✓ | ✓ | ✓ | **8.6** | OK |
| 6 | `notebooks/01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb` | Pipeline IoT | 03 | Validación Telegraf → InfluxDB → Grafana | plata | Golden set chatbot (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **7.6** | OK |
| 7 | `notebooks/02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb` | Forecasting | 01 | Caso B · 01 EDA del consumo eléctrico horario | bronce | BDG2 educational (público resampled) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | ✓ | ✓ | ✓ | ✓ | ✓ | **8.8** | OK |
| 8 | `notebooks/02_case_B_energy_forecasting/02_bronze_to_silver_energy.ipynb` | Forecasting | 02 | Caso B · 02 ETL bronce → plata para consumo e… | bronce → plata | BDG2 educational (público resampled) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **7.9** | OK |
| 9 | `notebooks/02_case_B_energy_forecasting/03_features_forecasting.ipynb` | Forecasting | 03 | Caso B · 03 Features para forecasting horario | oro | BDG2 educational (público resampled) | captia_schema, connection, plotting, synthetic_mocks | 23/7 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 10 | `notebooks/02_case_B_energy_forecasting/04_baseline_sarima_xgboost_lstm.ipynb` | Forecasting | 04 | Caso B · 04 Baselines SARIMA / XGBoost / LSTM… | oro | BDG2 educational (público resampled), Golden set chatbot (sintético) | captia_schema, connection, eval_helpers, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.7** | OK |
| 11 | `notebooks/02_case_B_energy_forecasting/05_validacion_modelo_24h.ipynb` | Forecasting | 05 | Caso B · 05 Validación 24h — walk-forward y m… | oro | BDG2 educational (público resampled) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | — | **7.7** | OK |
| 12 | `notebooks/03_case_C_hvac_anomaly_detection/01_eda_hvac_fdd.ipynb` | Anomaly Detection | 01 | Caso C · 01 EDA HVAC y catálogo de fallos | bronce | LBNL FDD RTU (público mockeado) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.6** | OK |
| 13 | `notebooks/03_case_C_hvac_anomaly_detection/02_bronze_to_silver_hvac.ipynb` | Anomaly Detection | 02 | Caso C · 02 ETL bronce → plata HVAC + etiquet… | bronce → plata | LBNL FDD RTU (público mockeado) | captia_schema, connection, plotting, synthetic_mocks | 23/7 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 14 | `notebooks/03_case_C_hvac_anomaly_detection/03_features_anomalias_hvac.ipynb` | Anomaly Detection | 03 | Caso C · 03 Features para detección de anomal… | oro | LBNL FDD RTU (público mockeado) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.4** | OK |
| 15 | `notebooks/03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder.ipynb` | Anomaly Detection | 04 | Caso C · 04 Isolation Forest + Autoencoder | oro | Golden set chatbot (sintético), LBNL FDD RTU (público mockeado) | captia_schema, connection, diagnostic_plots, eval_helpers, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **9.3** | OK |
| 16 | `notebooks/03_case_C_hvac_anomaly_detection/05_validacion_fallos_etiquetados.ipynb` | Anomaly Detection | 05 | Caso C · 05 Validación supervisada con etique… | oro | LBNL FDD RTU (público mockeado) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 66.7% | — | ✓ | ✓ | ✓ | ✓ | **8.3** | OK |
| 17 | `notebooks/04_case_D_iaq_occupancy/01_eda_iaq_ocupacion.ipynb` | IAQ + Occupancy | 01 | Caso D · 01 EDA IAQ y ocupación en aulas | bronce | In-Gauge AULA01 (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/5 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.6** | OK |
| 18 | `notebooks/04_case_D_iaq_occupancy/02_bronze_to_silver_iaq.ipynb` | IAQ + Occupancy | 02 | Caso D · 02 ETL bronce → plata IAQ + poblar c… | bronce → plata | DGT cameras (sintético), Golden set chatbot (sintético), In-Gauge AULA01 (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/7 | 22 | 85.7% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 19 | `notebooks/04_case_D_iaq_occupancy/03_features_confort_ocupacion.ipynb` | IAQ + Occupancy | 03 | Caso D · 03 Features para predicción de ocupa… | oro | In-Gauge AULA01 (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.5** | OK |
| 20 | `notebooks/04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente.ipynb` | IAQ + Occupancy | 04 | Caso D · 04 Modelo de ocupación desde ambient… | oro | Golden set chatbot (sintético), In-Gauge AULA01 (sintético) | captia_schema, connection, diagnostic_plots, eval_helpers, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **9.6** | OK |
| 21 | `notebooks/04_case_D_iaq_occupancy/05_validacion_iaq_confort.ipynb` | IAQ + Occupancy | 05 | Caso D · 05 Alertas IAQ con histéresis y jera… | oro | ERA5 Xàtiva (público mockeado), In-Gauge AULA01 (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **7.9** | OK |
| 22 | `notebooks/05_case_E_weather_solar/01_eda_era5.ipynb` | Weather + Solar | 01 | Caso E · 01 EDA ERA5 Xàtiva (mock) | bronce | ERA5 Xàtiva (público mockeado), Golden set chatbot (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/5 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **7.8** | OK |
| 23 | `notebooks/05_case_E_weather_solar/02_bronze_to_silver_weather.ipynb` | Weather + Solar | 02 | Caso E · 02 ETL ERA5 → CAPTIA weather_station | bronce → plata | ERA5 Xàtiva (público mockeado) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **7.9** | OK |
| 24 | `notebooks/05_case_E_weather_solar/03_features_meteorologicas.ipynb` | Weather + Solar | 03 | Caso E · 03 Features meteorológicos para Caso… | oro | ERA5 Xàtiva (público mockeado) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.0** | OK |
| 25 | `notebooks/05_case_E_weather_solar/04_prediccion_solar.ipynb` | Weather + Solar | 04 | Caso E · 04 Predicción solar — clear-sky deco… | oro | ERA5 Xàtiva (público mockeado), Golden set chatbot (sintético) | captia_schema, connection, diagnostic_plots, eval_helpers, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.7** | OK |
| 26 | `notebooks/06_case_F_mlops/01_mlflow_lakefs_overview.ipynb` | MLOps | 01 | Caso F · 01 MLflow + lakeFS — visión general | transversal | — | captia_schema, connection, plotting, synthetic_mocks | 23/7 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **7.7** | OK |
| 27 | `notebooks/06_case_F_mlops/02_tracking_experimentos.ipynb` | MLOps | 02 | Caso F · 02 Tracking de experimentos con MLfl… | transversal | BDG2 educational (público resampled) | captia_schema, connection, eval_helpers, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 28 | `notebooks/06_case_F_mlops/03_reproducibilidad_datasets_modelos.ipynb` | MLOps | 03 | Caso F · 03 Reproducibilidad — hash dataset, … | transversal | BDG2 educational (público resampled) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 83.3% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 29 | `notebooks/07_case_G_data_quality_agents/01_reglas_calidad_bronce.ipynb` | Data Quality + Agents | 01 | Caso G · 01 Reglas de calidad sobre la capa b… | bronce | BDG2 educational (público resampled), In-Gauge AULA01 (sintético), LBNL FDD RTU (público mockeado) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 30 | `notebooks/07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb.ipynb` | Data Quality + Agents | 02 | Caso G · 02 Reglas Flux sobre la capa plata | plata | In-Gauge AULA01 (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **7.6** | OK |
| 31 | `notebooks/07_case_G_data_quality_agents/03_reglas_calidad_oro_ml.ipynb` | Data Quality + Agents | 03 | Caso G · 03 Calidad sobre la capa oro (datase… | oro | BDG2 educational (público resampled) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.5** | NEEDS_REWRITE |
| 32 | `notebooks/07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb` | Data Quality + Agents | 04 | Caso G · 04 Agentes especialistas de calidad … | transversal | Golden set chatbot (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.3** | OK |
| 33 | `notebooks/08_case_H_rag_chatbot/01_arquitectura_rag_tools.ipynb` | RAG + Chatbot | 01 | Caso H · 01 Arquitectura del chatbot — tools … | oro | Golden set chatbot (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/4 | 22 | 100.0% | — | ✓ | ✓ | ✓ | — | **7.7** | OK |
| 34 | `notebooks/08_case_H_rag_chatbot/02_tools_influxdb.ipynb` | RAG + Chatbot | 02 | Caso H · 02 Tools sobre InfluxDB | oro | Golden set chatbot (sintético), In-Gauge AULA01 (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | — | **8.0** | NEEDS_REWRITE |
| 35 | `notebooks/08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos.ipynb` | RAG + Chatbot | 03 | Caso H · 03 Tools mock para modelos predictiv… | oro | Golden set chatbot (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/4 | 22 | 75.0% | — | ✓ | ✓ | ✓ | — | **7.8** | OK |
| 36 | `notebooks/08_case_H_rag_chatbot/04_rag_documental.ipynb` | RAG + Chatbot | 04 | Caso H · 04 RAG documental — TF-IDF como sust… | oro | Golden set chatbot (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.8** | NEEDS_REWRITE |
| 37 | `notebooks/08_case_H_rag_chatbot/05_evaluacion_chatbot.ipynb` | RAG + Chatbot | 05 | Caso H · 05 Evaluación del chatbot con golden… | oro | BDG2 educational (público resampled), Golden set chatbot (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.2** | NEEDS_REWRITE |
| 38 | `notebooks/09_case_I_spark_vs_pandas/01_bdg2_overview.ipynb` | Big Data | 01 | Caso I · 01 BDG2 overview — el dataset de 53M… | bronce | BDG2 educational (público resampled) | captia_schema, connection, plotting, synthetic_mocks | 23/5 | 22 | 80.0% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 39 | `notebooks/09_case_I_spark_vs_pandas/02_benchmark_pandas.ipynb` | Big Data | 02 | Caso I · 02 Benchmark con pandas | bronce → plata | BDG2 educational (público resampled) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 66.7% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 40 | `notebooks/09_case_I_spark_vs_pandas/03_benchmark_spark.ipynb` | Big Data | 03 | Caso I · 03 Benchmark con Spark (o Dask como … | bronce → plata | BDG2 educational (público resampled) | captia_schema, connection, plotting, synthetic_mocks | 23/7 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **7.8** | NEEDS_REWRITE |
| 41 | `notebooks/09_case_I_spark_vs_pandas/04_comparativa_resultados.ipynb` | Big Data | 04 | Caso I · 04 Benchmark medido — pandas vs pola… | oro | BDG2 educational (público resampled), DGT cameras (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 83.3% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 42 | `notebooks/10_case_J_traffic_yolo/01_captura_imagenes_dgt.ipynb` | Computer Vision | 01 | Caso J · 01 Captura de imágenes DGT — estrate… | bronce | DGT cameras (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/7 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **7.8** | NEEDS_REWRITE |
| 43 | `notebooks/10_case_J_traffic_yolo/02_inferencia_yolo.ipynb` | Computer Vision | 02 | Caso J · 02 Inferencia YOLO (mock por defecto… | bronce → plata | DGT cameras (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 83.3% | — | ✓ | ✓ | ✓ | ✓ | **8.0** | NEEDS_REWRITE |
| 44 | `notebooks/10_case_J_traffic_yolo/03_series_temporales_trafico.ipynb` | Computer Vision | 03 | Caso J · 03 Series temporales en InfluxDB par… | bronce → plata | DGT cameras (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.1** | OK |
| 45 | `notebooks/10_case_J_traffic_yolo/04_integracion_meteo_trafico.ipynb` | Computer Vision | 04 | Caso J · 04 Predicción congestión a 15 min — … | oro | DGT cameras (sintético), Golden set chatbot (sintético) | captia_schema, connection, plotting, synthetic_mocks | 23/6 | 22 | 100.0% | — | ✓ | ✓ | ✓ | ✓ | **8.6** | OK |

## Agregados por caso de uso

| Caso | # nb | Score medio | Outputs medio % | Cita schema | Mocks etiquetados | Sin secretos | Sin paths abs |
|---|---|---|---|---|---|---|---|
| `00_project_overview` | 3 | 8.37 | 100.0% | 3/3 | 0/3 | 3/3 | 3/3 |
| `01_case_A_pipeline_iot` | 3 | 8.03 | 100.0% | 3/3 | 1/3 | 3/3 | 3/3 |
| `02_case_B_energy_forecasting` | 5 | 8.24 | 100.0% | 5/5 | 1/5 | 5/5 | 5/5 |
| `03_case_C_hvac_anomaly_detection` | 5 | 8.54 | 93.3% | 5/5 | 0/5 | 5/5 | 5/5 |
| `04_case_D_iaq_occupancy` | 5 | 8.54 | 97.1% | 5/5 | 0/5 | 5/5 | 5/5 |
| `05_case_E_weather_solar` | 4 | 8.10 | 100.0% | 4/4 | 0/4 | 4/4 | 4/4 |
| `06_case_F_mlops` | 3 | 7.97 | 94.4% | 3/3 | 0/3 | 3/3 | 3/3 |
| `07_case_G_data_quality_agents` | 4 | 8.12 | 100.0% | 4/4 | 0/4 | 4/4 | 4/4 |
| `08_case_H_rag_chatbot` | 5 | 8.10 | 95.0% | 5/5 | 0/5 | 5/5 | 5/5 |
| `09_case_I_spark_vs_pandas` | 4 | 8.03 | 82.5% | 4/4 | 0/4 | 4/4 | 4/4 |
| `10_case_J_traffic_yolo` | 4 | 8.12 | 95.8% | 4/4 | 0/4 | 4/4 | 4/4 |

## Distribución por estado

| Estado | Notebooks | % |
|---|---|---|
| OK | 38 | 84.4% |
| NEEDS_REFACTOR | 0 | 0.0% |
| NEEDS_REWRITE | 7 | 15.6% |
| BROKEN | 0 | 0.0% |
| MISSING_CONTEXT | 0 | 0.0% |

## Glosario de columnas

- **Caso**: dominio temático (Pipeline IoT, Forecasting, etc.).
- **Etapa**: 01-EDA, 02-ETL, 03-Features, 04-Modelado, 05-Validación.
- **Capa Medallion**: bronce / plata / oro / transversal.
- **Datasets**: orígenes de datos detectados (sintético, público, mock).
- **Helpers `_common`**: módulos `notebooks._common.*` utilizados.
- **md / code**: nº celdas markdown / código.
- **Sec**: nº distintas secciones (debería ser 22 para todos).
- **Outputs %**: % de code cells con outputs persistidos.
- **Mocks**: ¿hay celdas etiquetadas con `# MOCK`?
- **Sin secretos**: regex no detecta tokens inline.
- **Sin paths abs**: no hay rutas absolutas Windows / Unix.
- **Cita schema**: menciona `captia_point` o el schema canónico.
- **Assert**: contiene al menos un `assert`.
- **Score**: nota global 0-10 (curado desde NOTEBOOK_AUDIT_DETAILED).
- **Estado**: OK / NEEDS_REFACTOR / NEEDS_REWRITE / BROKEN / MISSING_CONTEXT.

## Referencias cruzadas

- Auditoría detallada: [`../NOTEBOOK_AUDIT_DETAILED.md`](../NOTEBOOK_AUDIT_DETAILED.md).
- Reviews por notebook: [`reviews/`](reviews/).
- Matriz de calidad: [`NOTEBOOK_QUALITY_MATRIX.md`](NOTEBOOK_QUALITY_MATRIX.md).
- Plan de refactor: [`NOTEBOOK_REFACTOR_PLAN.md`](NOTEBOOK_REFACTOR_PLAN.md).
