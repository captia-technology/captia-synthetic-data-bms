# Auditoría — Reporte de ejecución de notebooks

> **Generado:** 2026-05-10T13:41:09.973143+00:00
> **Total notebooks:** 45
> **PASS:** 36 · **FAIL:** 9 · **TIMEOUT:** 0
> **Tiempo total:** 7.9 min (476 s)

## Resumen por caso de uso

| Caso | PASS | FAIL | TIMEOUT | Tiempo (s) |
|---|---:|---:|---:|---:|
| `00_project_overview` | 3 | 0 | 0 | 39 |
| `01_case_A_pipeline_iot` | 2 | 1 | 0 | 30 |
| `02_case_B_energy_forecasting` | 5 | 0 | 0 | 71 |
| `03_case_C_hvac_anomaly_detection` | 5 | 0 | 0 | 56 |
| `04_case_D_iaq_occupancy` | 4 | 1 | 0 | 49 |
| `05_case_E_weather_solar` | 4 | 0 | 0 | 35 |
| `06_case_F_mlops` | 3 | 0 | 0 | 40 |
| `07_case_G_data_quality_agents` | 3 | 1 | 0 | 44 |
| `08_case_H_rag_chatbot` | 1 | 4 | 0 | 48 |
| `09_case_I_spark_vs_pandas` | 3 | 1 | 0 | 31 |
| `10_case_J_traffic_yolo` | 3 | 1 | 0 | 32 |

## Detalle por notebook

| Notebook | Status | Tiempo (s) | Error (resumen) |
|---|---|---:|---|
| `notebooks/00_project_overview/00_arquitectura_medallion_captia.ipynb` | ✅ PASS | 7.0 | — |
| `notebooks/00_project_overview/01_schema_captia_influxdb.ipynb` | ✅ PASS | 13.2 | — |
| `notebooks/00_project_overview/02_conexion_influxdb_y_variables_entorno.ipynb` | ✅ PASS | 18.6 | — |
| `notebooks/01_case_A_pipeline_iot/01_explicacion_pipeline_centinela.ipynb` | ✅ PASS | 9.7 | — |
| `notebooks/01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb` | ✅ PASS | 8.9 | — |
| `notebooks/01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb` | ❌ FAIL | 11.7 | Traceback (most recent call last):     await self._check_raise_for_error(cell, cell_index, exec_reply)   File "C:\CAPTIA\CAPTIA-SYNTHETIC-DA… |
| `notebooks/02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb` | ✅ PASS | 11.7 | — |
| `notebooks/02_case_B_energy_forecasting/02_bronze_to_silver_energy.ipynb` | ✅ PASS | 10.0 | — |
| `notebooks/02_case_B_energy_forecasting/03_features_forecasting.ipynb` | ✅ PASS | 10.3 | — |
| `notebooks/02_case_B_energy_forecasting/04_baseline_sarima_xgboost_lstm.ipynb` | ✅ PASS | 15.6 | — |
| `notebooks/02_case_B_energy_forecasting/05_validacion_modelo_24h.ipynb` | ✅ PASS | 23.5 | — |
| `notebooks/03_case_C_hvac_anomaly_detection/01_eda_hvac_fdd.ipynb` | ✅ PASS | 8.7 | — |
| `notebooks/03_case_C_hvac_anomaly_detection/02_bronze_to_silver_hvac.ipynb` | ✅ PASS | 8.1 | — |
| `notebooks/03_case_C_hvac_anomaly_detection/03_features_anomalias_hvac.ipynb` | ✅ PASS | 9.1 | — |
| `notebooks/03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder.ipynb` | ✅ PASS | 18.8 | — |
| `notebooks/03_case_C_hvac_anomaly_detection/05_validacion_fallos_etiquetados.ipynb` | ✅ PASS | 11.0 | — |
| `notebooks/04_case_D_iaq_occupancy/01_eda_iaq_ocupacion.ipynb` | ✅ PASS | 8.5 | — |
| `notebooks/04_case_D_iaq_occupancy/02_bronze_to_silver_iaq.ipynb` | ❌ FAIL | 8.7 | Traceback (most recent call last):     await self._check_raise_for_error(cell, cell_index, exec_reply)   File "C:\CAPTIA\CAPTIA-SYNTHETIC-DA… |
| `notebooks/04_case_D_iaq_occupancy/03_features_confort_ocupacion.ipynb` | ✅ PASS | 8.9 | — |
| `notebooks/04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente.ipynb` | ✅ PASS | 12.6 | — |
| `notebooks/04_case_D_iaq_occupancy/05_validacion_iaq_confort.ipynb` | ✅ PASS | 10.1 | — |
| `notebooks/05_case_E_weather_solar/01_eda_era5.ipynb` | ✅ PASS | 9.3 | — |
| `notebooks/05_case_E_weather_solar/02_bronze_to_silver_weather.ipynb` | ✅ PASS | 8.7 | — |
| `notebooks/05_case_E_weather_solar/03_features_meteorologicas.ipynb` | ✅ PASS | 7.6 | — |
| `notebooks/05_case_E_weather_solar/04_prediccion_solar.ipynb` | ✅ PASS | 9.4 | — |
| `notebooks/06_case_F_mlops/01_mlflow_lakefs_overview.ipynb` | ✅ PASS | 7.5 | — |
| `notebooks/06_case_F_mlops/02_tracking_experimentos.ipynb` | ✅ PASS | 9.4 | — |
| `notebooks/06_case_F_mlops/03_reproducibilidad_datasets_modelos.ipynb` | ✅ PASS | 23.5 | — |
| `notebooks/07_case_G_data_quality_agents/01_reglas_calidad_bronce.ipynb` | ❌ FAIL | 6.9 | Traceback (most recent call last):     await self._check_raise_for_error(cell, cell_index, exec_reply)   File "C:\CAPTIA\CAPTIA-SYNTHETIC-DA… |
| `notebooks/07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb.ipynb` | ✅ PASS | 22.6 | — |
| `notebooks/07_case_G_data_quality_agents/03_reglas_calidad_oro_ml.ipynb` | ✅ PASS | 7.5 | — |
| `notebooks/07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb` | ✅ PASS | 7.3 | — |
| `notebooks/08_case_H_rag_chatbot/01_arquitectura_rag_tools.ipynb` | ❌ FAIL | 7.9 | [31mKeyError[39m                                  Traceback (most recent call last) [32m   3647[39m         [38;5;28;01mraise[39;00m I… |
| `notebooks/08_case_H_rag_chatbot/02_tools_influxdb.ipynb` | ❌ FAIL | 15.8 | [32m---> [39m[32m39[39m     [38;5;28;01mraise[39;00m value [32m    504[39m [38;5;66;03m# We are swallowing BrokenPipeError (errno.E… |
| `notebooks/08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos.ipynb` | ✅ PASS | 6.9 | — |
| `notebooks/08_case_H_rag_chatbot/04_rag_documental.ipynb` | ❌ FAIL | 9.2 | [31mKeyError[39m                                  Traceback (most recent call last) [32m   3647[39m         [38;5;28;01mraise[39;00m I… |
| `notebooks/08_case_H_rag_chatbot/05_evaluacion_chatbot.ipynb` | ❌ FAIL | 8.3 | [31mKeyError[39m                                  Traceback (most recent call last) [32m   3647[39m         [38;5;28;01mraise[39;00m I… |
| `notebooks/09_case_I_spark_vs_pandas/01_bdg2_overview.ipynb` | ✅ PASS | 10.3 | — |
| `notebooks/09_case_I_spark_vs_pandas/02_benchmark_pandas.ipynb` | ✅ PASS | 6.3 | — |
| `notebooks/09_case_I_spark_vs_pandas/03_benchmark_spark.ipynb` | ✅ PASS | 6.9 | — |
| `notebooks/09_case_I_spark_vs_pandas/04_comparativa_resultados.ipynb` | ❌ FAIL | 7.2 | Traceback (most recent call last):     await self._check_raise_for_error(cell, cell_index, exec_reply)   File "C:\CAPTIA\CAPTIA-SYNTHETIC-DA… |
| `notebooks/10_case_J_traffic_yolo/01_captura_imagenes_dgt.ipynb` | ❌ FAIL | 6.7 | Traceback (most recent call last):     await self._check_raise_for_error(cell, cell_index, exec_reply)   File "C:\CAPTIA\CAPTIA-SYNTHETIC-DA… |
| `notebooks/10_case_J_traffic_yolo/02_inferencia_yolo.ipynb` | ✅ PASS | 7.1 | — |
| `notebooks/10_case_J_traffic_yolo/03_series_temporales_trafico.ipynb` | ✅ PASS | 6.5 | — |
| `notebooks/10_case_J_traffic_yolo/04_integracion_meteo_trafico.ipynb` | ✅ PASS | 11.9 | — |

## Errores completos

### `notebooks/01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb` — FAIL

```
Traceback (most recent call last):
    await self._check_raise_for_error(cell, cell_index, exec_reply)
  File "C:\CAPTIA\CAPTIA-SYNTHETIC-DATA-BMS\.venv\Lib\site-packages\nbclient\client.py", line 918, in _check_raise_for_error
    raise CellExecutionError.from_cell_and_msg(cell, exec_reply_content)
nbclient.exceptions.CellExecutionError: An error occurred while executing the following cell:
[31mNameError[39m                                 Traceback (most recent call last)
[31mNameError[39m: name 'os' is not defined
```

### `notebooks/04_case_D_iaq_occupancy/02_bronze_to_silver_iaq.ipynb` — FAIL

```
Traceback (most recent call last):
    await self._check_raise_for_error(cell, cell_index, exec_reply)
  File "C:\CAPTIA\CAPTIA-SYNTHETIC-DATA-BMS\.venv\Lib\site-packages\nbclient\client.py", line 918, in _check_raise_for_error
    raise CellExecutionError.from_cell_and_msg(cell, exec_reply_content)
nbclient.exceptions.CellExecutionError: An error occurred while executing the following cell:
[31mIndexError[39m                                Traceback (most recent call last)
[31mIndexError[39m: list index out of range
```

### `notebooks/07_case_G_data_quality_agents/01_reglas_calidad_bronce.ipynb` — FAIL

```
Traceback (most recent call last):
    await self._check_raise_for_error(cell, cell_index, exec_reply)
  File "C:\CAPTIA\CAPTIA-SYNTHETIC-DATA-BMS\.venv\Lib\site-packages\nbclient\client.py", line 918, in _check_raise_for_error
    raise CellExecutionError.from_cell_and_msg(cell, exec_reply_content)
nbclient.exceptions.CellExecutionError: An error occurred while executing the following cell:
[31mAttributeError[39m                            Traceback (most recent call last)
[31mAttributeError[39m: 'DataFrame' object has no attribute 'applymap'
```

### `notebooks/08_case_H_rag_chatbot/01_arquitectura_rag_tools.ipynb` — FAIL

```
[31mKeyError[39m                                  Traceback (most recent call last)
[32m   3647[39m         [38;5;28;01mraise[39;00m InvalidIndexError(key) [38;5;28;01mfrom[39;00m[38;5;250m [39m[34;01merr[39;00m
[32m-> [39m[32m3648[39m     [38;5;28;01mraise[39;00m [38;5;167;01mKeyError[39;00m(key) [38;5;28;01mfrom[39;00m[38;5;250m [39m[34;01merr[39;00m
[32m   3649[39m [38;5;28;01mexcept[39;00m [38;5;167;01mTypeError[39;00m:
[32m   3650[39m     [38;5;66;03m# If we have a listlike key, _check_indexing_error will raise[39;00m
[32m   3651[39m     [38;5;66;03m#  InvalidIndexError. Otherwise we fall through and re-raise[39;00m
[32m   3652[39m     [38;5;66;03m#  the TypeError.[39;00m
[31mKeyError[39m: 'category'
```

### `notebooks/08_case_H_rag_chatbot/02_tools_influxdb.ipynb` — FAIL

```
[32m---> [39m[32m39[39m     [38;5;28;01mraise[39;00m value
[32m    504[39m [38;5;66;03m# We are swallowing BrokenPipeError (errno.EPIPE) since the server is[39;00m
[32m    507[39m [38;5;28;01mexcept[39;00m [38;5;167;01mBrokenPipeError[39;00m:
[32m   1332[39m     [38;5;28;01mraise[39;00m CannotSendHeader()
[32m   1039[39m         [38;5;28;01mraise[39;00m NotConnected()
[32m--> [39m[32m211[39m     [38;5;28;01mraise[39;00m NameResolutionError([38;5;28mself[39m.host, [38;5;28mself[39m, e) [38;5;28;01mfrom[39;00m[38;5;250m [39m[34;01me[39;00m
[32m    213[39m     [38;5;28;01mraise[39;00m ConnectTimeoutError(
[31mNameResolutionError[39m: HTTPConnection(host='influxdb', port=8086): Failed to resolve 'influxdb' ([Errno 11001] getaddrinfo failed)
```

### `notebooks/08_case_H_rag_chatbot/04_rag_documental.ipynb` — FAIL

```
[31mKeyError[39m                                  Traceback (most recent call last)
[32m   3647[39m         [38;5;28;01mraise[39;00m InvalidIndexError(key) [38;5;28;01mfrom[39;00m[38;5;250m [39m[34;01merr[39;00m
[32m-> [39m[32m3648[39m     [38;5;28;01mraise[39;00m [38;5;167;01mKeyError[39;00m(key) [38;5;28;01mfrom[39;00m[38;5;250m [39m[34;01merr[39;00m
[32m   3649[39m [38;5;28;01mexcept[39;00m [38;5;167;01mTypeError[39;00m:
[32m   3650[39m     [38;5;66;03m# If we have a listlike key, _check_indexing_error will raise[39;00m
[32m   3651[39m     [38;5;66;03m#  InvalidIndexError. Otherwise we fall through and re-raise[39;00m
[32m   3652[39m     [38;5;66;03m#  the TypeError.[39;00m
[31mKeyError[39m: 'expected_mechanism'
```

### `notebooks/08_case_H_rag_chatbot/05_evaluacion_chatbot.ipynb` — FAIL

```
[31mKeyError[39m                                  Traceback (most recent call last)
[32m   3647[39m         [38;5;28;01mraise[39;00m InvalidIndexError(key) [38;5;28;01mfrom[39;00m[38;5;250m [39m[34;01merr[39;00m
[32m-> [39m[32m3648[39m     [38;5;28;01mraise[39;00m [38;5;167;01mKeyError[39;00m(key) [38;5;28;01mfrom[39;00m[38;5;250m [39m[34;01merr[39;00m
[32m   3649[39m [38;5;28;01mexcept[39;00m [38;5;167;01mTypeError[39;00m:
[32m   3650[39m     [38;5;66;03m# If we have a listlike key, _check_indexing_error will raise[39;00m
[32m   3651[39m     [38;5;66;03m#  InvalidIndexError. Otherwise we fall through and re-raise[39;00m
[32m   3652[39m     [38;5;66;03m#  the TypeError.[39;00m
[31mKeyError[39m: 'category'
```

### `notebooks/09_case_I_spark_vs_pandas/04_comparativa_resultados.ipynb` — FAIL

```
Traceback (most recent call last):
    await self._check_raise_for_error(cell, cell_index, exec_reply)
  File "C:\CAPTIA\CAPTIA-SYNTHETIC-DATA-BMS\.venv\Lib\site-packages\nbclient\client.py", line 918, in _check_raise_for_error
    raise CellExecutionError.from_cell_and_msg(cell, exec_reply_content)
nbclient.exceptions.CellExecutionError: An error occurred while executing the following cell:
[31mAssertionError[39m                            Traceback (most recent call last)
[31mAssertionError[39m:
```

### `notebooks/10_case_J_traffic_yolo/01_captura_imagenes_dgt.ipynb` — FAIL

```
Traceback (most recent call last):
    await self._check_raise_for_error(cell, cell_index, exec_reply)
  File "C:\CAPTIA\CAPTIA-SYNTHETIC-DATA-BMS\.venv\Lib\site-packages\nbclient\client.py", line 918, in _check_raise_for_error
    raise CellExecutionError.from_cell_and_msg(cell, exec_reply_content)
nbclient.exceptions.CellExecutionError: An error occurred while executing the following cell:
[31mAssertionError[39m                            Traceback (most recent call last)
[31mAssertionError[39m:
```
