# Auditoría — Reporte de ejecución de notebooks

> **Generado:** 2026-05-10T14:00:15.949652+00:00
> **Total notebooks:** 45
> **PASS:** 45 · **FAIL:** 0 · **TIMEOUT:** 0
> **Tiempo total:** 8.8 min (530 s)

## Resumen por caso de uso

| Caso | PASS | FAIL | TIMEOUT | Tiempo (s) |
|---|---:|---:|---:|---:|
| `00_project_overview` | 3 | 0 | 0 | 32 |
| `01_case_A_pipeline_iot` | 3 | 0 | 0 | 33 |
| `02_case_B_energy_forecasting` | 5 | 0 | 0 | 71 |
| `03_case_C_hvac_anomaly_detection` | 5 | 0 | 0 | 68 |
| `04_case_D_iaq_occupancy` | 5 | 0 | 0 | 59 |
| `05_case_E_weather_solar` | 4 | 0 | 0 | 48 |
| `06_case_F_mlops` | 3 | 0 | 0 | 55 |
| `07_case_G_data_quality_agents` | 4 | 0 | 0 | 43 |
| `08_case_H_rag_chatbot` | 5 | 0 | 0 | 45 |
| `09_case_I_spark_vs_pandas` | 4 | 0 | 0 | 39 |
| `10_case_J_traffic_yolo` | 4 | 0 | 0 | 38 |

## Detalle por notebook

| Notebook | Status | Tiempo (s) | Error (resumen) |
|---|---|---:|---|
| `notebooks/00_project_overview/00_arquitectura_medallion_captia.ipynb` | ✅ PASS | 10.5 | — |
| `notebooks/00_project_overview/01_schema_captia_influxdb.ipynb` | ✅ PASS | 11.3 | — |
| `notebooks/00_project_overview/02_conexion_influxdb_y_variables_entorno.ipynb` | ✅ PASS | 10.1 | — |
| `notebooks/01_case_A_pipeline_iot/01_explicacion_pipeline_centinela.ipynb` | ✅ PASS | 10.9 | — |
| `notebooks/01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb` | ✅ PASS | 10.5 | — |
| `notebooks/01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb` | ✅ PASS | 12.1 | — |
| `notebooks/02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb` | ✅ PASS | 11.0 | — |
| `notebooks/02_case_B_energy_forecasting/02_bronze_to_silver_energy.ipynb` | ✅ PASS | 11.5 | — |
| `notebooks/02_case_B_energy_forecasting/03_features_forecasting.ipynb` | ✅ PASS | 10.8 | — |
| `notebooks/02_case_B_energy_forecasting/04_baseline_sarima_xgboost_lstm.ipynb` | ✅ PASS | 14.0 | — |
| `notebooks/02_case_B_energy_forecasting/05_validacion_modelo_24h.ipynb` | ✅ PASS | 23.9 | — |
| `notebooks/03_case_C_hvac_anomaly_detection/01_eda_hvac_fdd.ipynb` | ✅ PASS | 10.7 | — |
| `notebooks/03_case_C_hvac_anomaly_detection/02_bronze_to_silver_hvac.ipynb` | ✅ PASS | 10.9 | — |
| `notebooks/03_case_C_hvac_anomaly_detection/03_features_anomalias_hvac.ipynb` | ✅ PASS | 10.8 | — |
| `notebooks/03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder.ipynb` | ✅ PASS | 20.8 | — |
| `notebooks/03_case_C_hvac_anomaly_detection/05_validacion_fallos_etiquetados.ipynb` | ✅ PASS | 14.3 | — |
| `notebooks/04_case_D_iaq_occupancy/01_eda_iaq_ocupacion.ipynb` | ✅ PASS | 10.5 | — |
| `notebooks/04_case_D_iaq_occupancy/02_bronze_to_silver_iaq.ipynb` | ✅ PASS | 11.1 | — |
| `notebooks/04_case_D_iaq_occupancy/03_features_confort_ocupacion.ipynb` | ✅ PASS | 10.3 | — |
| `notebooks/04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente.ipynb` | ✅ PASS | 15.3 | — |
| `notebooks/04_case_D_iaq_occupancy/05_validacion_iaq_confort.ipynb` | ✅ PASS | 11.4 | — |
| `notebooks/05_case_E_weather_solar/01_eda_era5.ipynb` | ✅ PASS | 11.2 | — |
| `notebooks/05_case_E_weather_solar/02_bronze_to_silver_weather.ipynb` | ✅ PASS | 11.0 | — |
| `notebooks/05_case_E_weather_solar/03_features_meteorologicas.ipynb` | ✅ PASS | 11.2 | — |
| `notebooks/05_case_E_weather_solar/04_prediccion_solar.ipynb` | ✅ PASS | 14.1 | — |
| `notebooks/06_case_F_mlops/01_mlflow_lakefs_overview.ipynb` | ✅ PASS | 9.8 | — |
| `notebooks/06_case_F_mlops/02_tracking_experimentos.ipynb` | ✅ PASS | 13.1 | — |
| `notebooks/06_case_F_mlops/03_reproducibilidad_datasets_modelos.ipynb` | ✅ PASS | 31.8 | — |
| `notebooks/07_case_G_data_quality_agents/01_reglas_calidad_bronce.ipynb` | ✅ PASS | 10.9 | — |
| `notebooks/07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb.ipynb` | ✅ PASS | 10.1 | — |
| `notebooks/07_case_G_data_quality_agents/03_reglas_calidad_oro_ml.ipynb` | ✅ PASS | 11.8 | — |
| `notebooks/07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb` | ✅ PASS | 10.5 | — |
| `notebooks/08_case_H_rag_chatbot/01_arquitectura_rag_tools.ipynb` | ✅ PASS | 8.5 | — |
| `notebooks/08_case_H_rag_chatbot/02_tools_influxdb.ipynb` | ✅ PASS | 8.5 | — |
| `notebooks/08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos.ipynb` | ✅ PASS | 8.6 | — |
| `notebooks/08_case_H_rag_chatbot/04_rag_documental.ipynb` | ✅ PASS | 11.4 | — |
| `notebooks/08_case_H_rag_chatbot/05_evaluacion_chatbot.ipynb` | ✅ PASS | 8.1 | — |
| `notebooks/09_case_I_spark_vs_pandas/01_bdg2_overview.ipynb` | ✅ PASS | 9.6 | — |
| `notebooks/09_case_I_spark_vs_pandas/02_benchmark_pandas.ipynb` | ✅ PASS | 9.5 | — |
| `notebooks/09_case_I_spark_vs_pandas/03_benchmark_spark.ipynb` | ✅ PASS | 10.0 | — |
| `notebooks/09_case_I_spark_vs_pandas/04_comparativa_resultados.ipynb` | ✅ PASS | 9.9 | — |
| `notebooks/10_case_J_traffic_yolo/01_captura_imagenes_dgt.ipynb` | ✅ PASS | 8.1 | — |
| `notebooks/10_case_J_traffic_yolo/02_inferencia_yolo.ipynb` | ✅ PASS | 8.2 | — |
| `notebooks/10_case_J_traffic_yolo/03_series_temporales_trafico.ipynb` | ✅ PASS | 8.8 | — |
| `notebooks/10_case_J_traffic_yolo/04_integracion_meteo_trafico.ipynb` | ✅ PASS | 12.6 | — |