# Matriz de calidad de notebooks

> **Última verificación:** 2026-05-10  
> **Generado por:** `scripts/audit_notebooks.py --matrix`  
> **Score medio:** 8.22 / 10 (baseline 6.31; post Sprint 4 estimado).

Matriz **45 filas × 21 columnas** evaluando los 3 ejes corporativos CAPTIA:

1. **Técnica**: reproducibilidad, validaciones, schema, modelos, métricas.
2. **Didáctica**: progresión, contexto, interpretación, ejercicios.
3. **Corporativa**: portada, ROI auditable, alineación CENTINELA+.

Cada columna es **binaria** (✓/—) o **numérica** (0-10) o **categórica** (B/I/A · P0/P1/P2/OK).

## Tabla principal

| # | Notebook | Portada | Obj | Caso | CENTINELA+ | Medallion | `.env` | Sin secret | Sin abs | Valida | Schema | EDA | Viz interp | Concl | Ejerc | Ejecuta | Outputs | Riesgos | Nivel | Tec | Did | Corp | Prio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `00_project_overview/00_arquitectura_medallion_captia.ipynb` | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **8.5** | **9.0** | **10.0** | OK |
| 2 | `00_project_overview/01_schema_captia_influxdb.ipynb` | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **8.5** | **9.0** | **10.0** | P2 |
| 3 | `00_project_overview/02_conexion_influxdb_y_variables_entorno.ipynb` | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | I | **8.5** | **9.0** | **10.0** | P2 |
| 4 | `01_case_A_pipeline_iot/01_explicacion_pipeline_centinela.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **8.5** | **8.5** | **9.0** | P2 |
| 5 | `01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | I | **8.5** | **9.0** | **10.0** | OK |
| 6 | `01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **8.5** | **8.5** | **9.0** | P2 |
| 7 | `02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **8.5** | **9.0** | **10.0** | OK |
| 8 | `02_case_B_energy_forecasting/02_bronze_to_silver_energy.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | I | **8.5** | **8.5** | **9.0** | P2 |
| 9 | `02_case_B_energy_forecasting/03_features_forecasting.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **8.5** | **9.0** | **10.0** | P2 |
| 10 | `02_case_B_energy_forecasting/04_baseline_sarima_xgboost_lstm.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **10.0** | **9.0** | **10.0** | OK |
| 11 | `02_case_B_energy_forecasting/05_validacion_modelo_24h.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **8.5** | **8.5** | **9.0** | P2 |
| 12 | `03_case_C_hvac_anomaly_detection/01_eda_hvac_fdd.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **8.5** | **9.0** | **10.0** | OK |
| 13 | `03_case_C_hvac_anomaly_detection/02_bronze_to_silver_hvac.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | I | **8.5** | **9.0** | **10.0** | P2 |
| 14 | `03_case_C_hvac_anomaly_detection/03_features_anomalias_hvac.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **8.5** | **9.0** | **10.0** | P2 |
| 15 | `03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **10.0** | **9.0** | **10.0** | OK |
| 16 | `03_case_C_hvac_anomaly_detection/05_validacion_fallos_etiquetados.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | — | ✓ | A | **8.0** | **9.0** | **9.5** | P2 |
| 17 | `04_case_D_iaq_occupancy/01_eda_iaq_ocupacion.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **9.0** | **9.0** | **10.0** | OK |
| 18 | `04_case_D_iaq_occupancy/02_bronze_to_silver_iaq.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | I | **8.5** | **9.0** | **9.5** | P2 |
| 19 | `04_case_D_iaq_occupancy/03_features_confort_ocupacion.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **9.0** | **9.0** | **10.0** | OK |
| 20 | `04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **10.0** | **9.0** | **10.0** | OK |
| 21 | `04_case_D_iaq_occupancy/05_validacion_iaq_confort.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **9.0** | **8.5** | **9.0** | P2 |
| 22 | `05_case_E_weather_solar/01_eda_era5.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **8.5** | **8.5** | **9.0** | P2 |
| 23 | `05_case_E_weather_solar/02_bronze_to_silver_weather.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | I | **8.5** | **8.5** | **9.0** | P2 |
| 24 | `05_case_E_weather_solar/03_features_meteorologicas.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **8.5** | **9.0** | **10.0** | P2 |
| 25 | `05_case_E_weather_solar/04_prediccion_solar.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **9.5** | **9.0** | **10.0** | OK |
| 26 | `06_case_F_mlops/01_mlflow_lakefs_overview.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **8.5** | **8.5** | **9.0** | P2 |
| 27 | `06_case_F_mlops/02_tracking_experimentos.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | I | **9.0** | **9.0** | **10.0** | P2 |
| 28 | `06_case_F_mlops/03_reproducibilidad_datasets_modelos.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **8.0** | **9.0** | **9.5** | P2 |
| 29 | `07_case_G_data_quality_agents/01_reglas_calidad_bronce.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **8.5** | **9.0** | **10.0** | P2 |
| 30 | `07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | I | **8.5** | **8.5** | **9.0** | P2 |
| 31 | `07_case_G_data_quality_agents/03_reglas_calidad_oro_ml.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **7.0** | **9.0** | **10.0** | OK |
| 32 | `07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **8.5** | **9.0** | **10.0** | P2 |
| 33 | `08_case_H_rag_chatbot/01_arquitectura_rag_tools.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **8.0** | **8.5** | **9.0** | P2 |
| 34 | `08_case_H_rag_chatbot/02_tools_influxdb.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | I | **6.5** | **9.0** | **10.0** | P2 |
| 35 | `08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | A | **7.5** | **8.5** | **8.5** | P2 |
| 36 | `08_case_H_rag_chatbot/04_rag_documental.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **7.0** | **9.0** | **10.0** | OK |
| 37 | `08_case_H_rag_chatbot/05_evaluacion_chatbot.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **7.0** | **9.0** | **10.0** | P2 |
| 38 | `09_case_I_spark_vs_pandas/01_bdg2_overview.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **8.0** | **9.0** | **9.5** | P2 |
| 39 | `09_case_I_spark_vs_pandas/02_benchmark_pandas.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | — | ✓ | I | **8.0** | **9.0** | **9.5** | P2 |
| 40 | `09_case_I_spark_vs_pandas/03_benchmark_spark.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **7.0** | **8.5** | **9.0** | P2 |
| 41 | `09_case_I_spark_vs_pandas/04_comparativa_resultados.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **8.0** | **9.0** | **9.5** | P2 |
| 42 | `10_case_J_traffic_yolo/01_captura_imagenes_dgt.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | B | **7.0** | **8.5** | **9.0** | P2 |
| 43 | `10_case_J_traffic_yolo/02_inferencia_yolo.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | I | **6.5** | **9.0** | **9.5** | P2 |
| 44 | `10_case_J_traffic_yolo/03_series_temporales_trafico.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **8.5** | **9.0** | **10.0** | P2 |
| 45 | `10_case_J_traffic_yolo/04_integracion_meteo_trafico.ipynb` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | A | **8.5** | **9.0** | **10.0** | OK |

## Top-10 (replicar disciplina)

| # | Notebook | Score | Por qué |
|---|---|---|---|
| 1 | `04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente.ipynb` | **9.6** | 3 baselines + TimeSeriesSplit + class_weight + IC bootstrap |
| 2 | `03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder.ipynb` | **9.3** | 4 modelos + AE solo normales + assertion comparativa |
| 3 | `02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb` | **8.8** | Score 8.8 — disciplina técnica + didáctica consistente |
| 4 | `08_case_H_rag_chatbot/04_rag_documental.ipynb` | **8.8** | TF-IDF ES + Recall@k + MRR + golden set etiquetado |
| 5 | `02_case_B_energy_forecasting/04_baseline_sarima_xgboost_lstm.ipynb` | **8.7** | Score 8.7 — disciplina técnica + didáctica consistente |
| 6 | `05_case_E_weather_solar/04_prediccion_solar.ipynb` | **8.7** | Clear-sky + 4 baselines + skill score + clip + máscara nocturna |
| 7 | `00_project_overview/00_arquitectura_medallion_captia.ipynb` | **8.6** | Score 8.6 — disciplina técnica + didáctica consistente |
| 8 | `01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb` | **8.6** | Score 8.6 — disciplina técnica + didáctica consistente |
| 9 | `03_case_C_hvac_anomaly_detection/01_eda_hvac_fdd.ipynb` | **8.6** | Score 8.6 — disciplina técnica + didáctica consistente |
| 10 | `04_case_D_iaq_occupancy/01_eda_iaq_ocupacion.ipynb` | **8.6** | Score 8.6 — disciplina técnica + didáctica consistente |

## Bottom-10 (intervención prioritaria)

| # | Notebook | Score | Razón principal | Prioridad |
|---|---|---|---|---|
| 1 | `01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb` | **7.6** | Score bajo 7.6; revisar review individual | P2 |
| 2 | `07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb.ipynb` | **7.6** | Esqueleto, en modo offline no produce nada | P2 |
| 3 | `02_case_B_energy_forecasting/05_validacion_modelo_24h.ipynb` | **7.7** | Mide pred puntual no forecast 24h | P2 |
| 4 | `06_case_F_mlops/01_mlflow_lakefs_overview.ipynb` | **7.7** | 0 líneas de código MLflow ejecutable | P2 |
| 5 | `08_case_H_rag_chatbot/01_arquitectura_rag_tools.ipynb` | **7.7** | Conceptual sin tabla decisional formal | P2 |
| 6 | `05_case_E_weather_solar/01_eda_era5.ipynb` | **7.8** | Score bajo 7.8; revisar review individual | P2 |
| 7 | `08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos.ipynb` | **7.8** | Score bajo 7.8; revisar review individual | P2 |
| 8 | `09_case_I_spark_vs_pandas/03_benchmark_spark.ipynb` | **7.8** | B7: `pyspark` y `dask` no instalados → DataFrame vacío entregado como artefacto ... | P2 |
| 9 | `10_case_J_traffic_yolo/01_captura_imagenes_dgt.ipynb` | **7.8** | B5: `fake_jpeg` crea `rng` interno → todas las imágenes idénticas (Alta) | P2 |
| 10 | `01_case_A_pipeline_iot/01_explicacion_pipeline_centinela.ipynb` | **7.9** | Score bajo 7.9; revisar review individual | P2 |

## Delta vs baseline (NOTEBOOK_AUDIT_DETAILED.md)

- **Score baseline (Sprint 0):** 6.31 / 10
- **Score actual:** 8.22 / 10
- **Delta:** +1.91 (+30.2%)

## Score global ponderado por dimensión

| Dimensión | Score medio | Peso | Score ponderado |
|---|---|---|---|
| Técnica | 8.32 | 0.40 | 3.33 |
| Didáctica | 8.86 | 0.40 | 3.54 |
| Corporativa | 9.62 | 0.20 | 1.92 |
| **Total ponderado** | — | 1.00 | **8.80** |
