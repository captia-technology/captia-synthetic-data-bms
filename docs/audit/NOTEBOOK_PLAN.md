# Plan de notebooks didácticos

> **Última verificación:** 2026-05-10
> **Audiencia:** profesores, alumnos del Curso de Especialización IES Simarro,
> mantenedores del repo, futuros usuarios CENTINELA+.
> **Filosofía:** cada notebook es material docente, no un script. Markdown
> abundante, diagramas Mermaid cuando ayuden, ejercicios al final, mocks
> claramente etiquetados como tales.

## Estructura de la carpeta `notebooks/`

```
notebooks/
├── _common/                       # helpers reutilizables (no notebooks)
│   ├── connection.py              # cliente InfluxDB con env vars
│   ├── captia_schema.py           # constantes del schema canónico
│   ├── synthetic_mocks.py         # generadores in-memory para no bloquear
│   └── plotting.py                # helpers matplotlib comunes
├── _data/                         # mocks ligeros por si no hay servicios
│   ├── ingauge_aula01_mock.csv
│   ├── era5_xativa_mock.csv
│   ├── bdg2_education_subset.csv
│   ├── lbnl_fdd_rtu_mock.csv
│   ├── docs_rag_seed/             # 12 markdowns para RAG
│   └── chatbot_golden_set.csv
├── 00_project_overview/
├── 01_case_A_pipeline_iot/
├── 02_case_B_energy_forecasting/
├── 03_case_C_hvac_anomaly_detection/
├── 04_case_D_iaq_occupancy/
├── 05_case_E_weather_solar/
├── 06_case_F_mlops/
├── 07_case_G_data_quality_agents/
├── 08_case_H_rag_chatbot/
├── 09_case_I_spark_vs_pandas/
└── 10_case_J_traffic_yolo/
```

## Estilo obligatorio en cada notebook

Cada `.ipynb` debe seguir esta plantilla (ver `notebooks/_common/template_outline.md`):

1. Título y objetivo (una frase clara).
2. Qué se aprende.
3. Contexto del caso de uso.
4. Relación con CENTINELA+ y AULA01.
5. Relación con Medallion (de qué capa lee, en qué capa escribe).
6. Datos de entrada (esperados + mocks).
7. Schema CAPTIA esperado.
8. Setup y variables de entorno (`.env` cargado).
9. Carga de datos o mocks.
10. Exploración paso a paso.
11. Transformación bronce → plata si aplica.
12. Construcción de capa oro si aplica.
13. Visualizaciones explicativas.
14. Validaciones.
15. Errores comunes.
16. Ejercicios propuestos.
17. Cómo se reutiliza con datos reales de CENTINELA+.
18. Resumen final + enlaces.

Para mantener la consistencia, el helper
`notebooks/_common/template_outline.md` lista los 18 encabezados que cada
notebook debe contener.

## Niveles

- **B (básico)** — sin código avanzado, foco en conceptos.
- **I (intermedio)** — código ETL/feature engineering típico.
- **A (avanzado)** — modelado ML, agentes, distribuido.

## Ejecutabilidad

- **ready** — el notebook se ejecuta de extremo a extremo solo con `numpy`,
  `pandas`, `matplotlib` (y opcionalmente `influxdb_client`).
- **needs-stack** — requiere stack `make demo` (Influx / MQTT) levantado.
- **mocked** — funciona con mocks; si los servicios reales están disponibles,
  documenta cómo cambiar al modo real.

## Catálogo

### `00_project_overview/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 0 | `00_arquitectura_medallion_captia.ipynb` | Visualizar bronce → plata → oro y mapear todos los casos. | Documentos del repo | Mermaid + tablas | — | B | ready | Schema canónico citado, capas correctas. |
| 1 | `01_schema_captia_influxdb.ipynb` | Entender el schema canónico (measurement, tags, field, buckets, metadata). | `02-domain-spec.md` | Tabla buckets + line protocol de ejemplo | 0 | B | ready | Topic estructura + tags presentes. |
| 2 | `02_conexion_influxdb_y_variables_entorno.ipynb` | Plantilla de conexión InfluxDB con `.env`; cómo NO hardcodear secretos. | `.env.example` | Función `get_client()` + smoke query | 1 | B | needs-stack (smoke) | Conexión activa o fallback mock. |

### `01_case_A_pipeline_iot/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_explicacion_pipeline_centinela.ipynb` | Diagramas + explicación de las 5 capas de CENTINELA+. | Guía CENTINELA+ §1 | Mermaid de cada capa | overview | B | ready | Cada capa documentada. |
| 2 | `02_publicacion_mqtt_a_influxdb.ipynb` | Publicar 100 mensajes MQTT con topic canónico y verificar llegada a Influx. | `paho-mqtt`, `mosquitto` | Conteo por aula en `telemetry` | 1 | I | needs-stack | `expected_count == actual_count`. |
| 3 | `03_validacion_telegraf_influx_grafana.ipynb` | Comprobar que Telegraf parsea topic, escribe en `captia_point` con 5 tags y la query Flux funciona. | Stack levantado | Resultado tag-by-tag | 2 | I | needs-stack | 5 tags + field `value`. |

### `02_case_B_energy_forecasting/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_eda_consumo_electrico.ipynb` | EDA `power_01`: ciclo diario, semanal, vacaciones, correlación T_ext. | `bdg2_education_subset.csv` | Histogramas + heatmap | overview | I | ready | Estacionariedad ADF. |
| 2 | `02_bronze_to_silver_energy.ipynb` | ETL BDG2 + UCI → `captia_point` en InfluxDB con tags correctos. | CSV BDG2 / UCI | Line protocol + smoke query | 1 | I | needs-stack | Cardinalidad tags + sin duplicados. |
| 3 | `03_features_forecasting.ipynb` | Features temporales (hora, dow, lag-24h, lag-168h, rolling 7d). | Plata | DataFrame oro | 2 | I | ready (offline) | NaN<5%; covariate balance. |
| 4 | `04_baseline_sarima_xgboost_lstm.ipynb` | Tres baselines comparados con MAE/MAPE/RMSE; LSTM opcional. | Oro | Métricas + plots residuos | 3 | A | ready (XGB), opcional LSTM | Sin leakage train/test temporal. |
| 5 | `05_validacion_modelo_24h.ipynb` | Walk-forward validation 24h; horizonte largo; rolling re-train. | 4 | Tabla métricas por horizonte | 4 | A | ready | MAPE 24h < baseline naive. |

### `03_case_C_hvac_anomaly_detection/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_eda_hvac_fdd.ipynb` | EDA LBNL FDD + sintético; tipos de fallo; firmas en sensores. | `lbnl_fdd_rtu_mock.csv` | Plots T_supply, ΔT, valve | overview | I | ready | 4 tipos de fallo identificados. |
| 2 | `02_bronze_to_silver_hvac.ipynb` | Mapping LBNL → CAPTIA + ingesta + etiquetas en `captia_fault_labels`. | LBNL CSV | Plata + labels | 1 | I | needs-stack | Etiquetas no contaminan `captia_point`. |
| 3 | `03_features_anomalias_hvac.ipynb` | Features ΔT (supply-return), duty cycle, ratio fan/valve. | Plata | DataFrame oro | 2 | I | ready (offline) | Distribución diferenciable normal vs fallo. |
| 4 | `04_isolation_forest_autoencoder.ipynb` | IF + AE entrenados; comparación; explicación con SHAP. | Oro | Modelos + métricas | 3 | A | ready | AUC > 0.85 sintético. |
| 5 | `05_validacion_fallos_etiquetados.ipynb` | Validación supervisada con etiquetas; matriz confusión por tipo. | 4 | Reporte | 4 | A | ready | Recall > 0.7 por tipo. |

### `04_case_D_iaq_occupancy/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_eda_iaq_ocupacion.ipynb` | EDA In-Gauge: CO2 vs ocupación, ciclo lectivo, recreos. | `ingauge_aula01_mock.csv` | Plots + decomposición | overview | B | ready | Picos CO2 alineados con horario. |
| 2 | `02_bronze_to_silver_iaq.ipynb` | Mapping In-Gauge → CAPTIA (tabla 1m); poblar `captia_point_meta`. | CSV | Plata + metadata | 1 | I | needs-stack | Metadata poblada → rollups OK. |
| 3 | `03_features_confort_ocupacion.ipynb` | Features: dCO2/dt, ratio T_in/T_out, IAQ index, lag features. | Plata | DataFrame oro | 2 | I | ready | Correlación CO2-occupancy > 0.5. |
| 4 | `04_modelo_ocupacion_desde_ambiente.ipynb` | Random Forest + Logistic baseline para `occupancy` desde ambiente. | Oro | Clasificador + métricas | 3 | I | ready | F1 > 0.8 In-Gauge. |
| 5 | `05_validacion_iaq_confort.ipynb` | IAQ aggregator + alertas según rangos OMS / EN 16798. | Plata | Reporte alertas | 4 | I | ready | Mapeo rango → categoría correcto. |

### `05_case_E_weather_solar/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_eda_era5.ipynb` | EDA ERA5 (mock) Xàtiva: T, GHI, viento, presión. | `era5_xativa_mock.csv` | Plots horarios anuales | overview | I | ready | Estacionalidad esperada. |
| 2 | `02_bronze_to_silver_weather.ipynb` | Conversión unidades + mapping a `weather_station/xativa/era5_gridpoint`. | NetCDF / mock | Plata | 1 | I | needs-stack | Tags + unidades SI. |
| 3 | `03_features_meteorologicas.ipynb` | Features para Caso B (T_ext, dT, GHI horario, dewpoint). | Plata | DataFrame | 2 | I | ready | Cobertura temporal sin gaps. |
| 4 | `04_prediccion_solar.ipynb` | Modelo predicción FV (regresor con T, GHI, hora, día año). | Oro | Modelo + curva diaria | 3 | I | ready | RMSE < 50 W/m². |

### `06_case_F_mlops/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_mlflow_lakefs_overview.ipynb` | Conceptos: experiment, run, artefacto, lakeFS tag. | docs | Diagrama | — | B | ready | — |
| 2 | `02_tracking_experimentos.ipynb` | Demo MLflow local (sqlite) con run completo Caso B-baseline. | Oro Caso B | Run registrado | 1 | I | ready | Métricas + artefactos persistidos. |
| 3 | `03_reproducibilidad_datasets_modelos.ipynb` | Versionado dataset (lakeFS-style con tag y hash) + reentrenar. | 2 | Hash idéntico | 2 | I | ready | Hash sha256 reproducible. |

### `07_case_G_data_quality_agents/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_reglas_calidad_bronce.ipynb` | Great Expectations sobre CSV originales (rangos, nulos, tipos). | CSV bronce | Suite GE + reporte | — | I | ready | Suite ejecutada sin error. |
| 2 | `02_reglas_calidad_plata_influxdb.ipynb` | Reglas Flux: completitud, rangos físicos, 5 tags presentes. | Plata | Reporte por variable | 1 | I | needs-stack | Sin variables fuera rango. |
| 3 | `03_reglas_calidad_oro_ml.ipynb` | Balance clases, leakage, distribución features train/test. | Oro Caso B/C/D | Checks | 2 | I | ready | KL-div train/test < umbral. |
| 4 | `04_agentes_especialistas_calidad.ipynb` | Agentes especialistas (mock): validate_silver, audit_mlflow, evaluate_chatbot. | Plata + Oro | Informes | 3 | A | mocked | Cada herramienta retorna JSON válido. |

### `08_case_H_rag_chatbot/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_arquitectura_rag_tools.ipynb` | Conceptos: tools vs RAG, decisión por tipo de pregunta. | docs | Mermaid + tabla | — | B | ready | Mapping pregunta → mecanismo. |
| 2 | `02_tools_influxdb.ipynb` | Implementación de `query_influxdb`, `compare_periods`, `get_building_state` con mocks. | Plata | Tools registradas | 1 | I | mocked | Firma estable. |
| 3 | `03_mock_tools_modelos_predictivos.ipynb` | Mocks para `get_weather_prediction`, `get_consumption_prediction`, `check_hvac_anomaly`. | — | Tools mock | 2 | I | mocked | Output formato esperado. |
| 4 | `04_rag_documental.ipynb` | Pipeline RAG mínimo: TF-IDF (mock embeddings) sobre 12 docs CENTINELA+ / OMS. | `docs_rag_seed/` | Retriever + ranker | 3 | I | ready | Recall@5 > 0.6 golden. |
| 5 | `05_evaluacion_chatbot.ipynb` | Golden set (40 preguntas) + métricas relevancia / coherencia / hallucination. | Tools + RAG + golden set | Reporte | 4 | A | ready | F1 > 0.6, hallucination < 0.2. |

### `09_case_I_spark_vs_pandas/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_bdg2_overview.ipynb` | Mapa BDG2: ficheros, tamaños, schema. | BDG2 metadata | Tablas | — | B | ready | — |
| 2 | `02_benchmark_pandas.ipynb` | Operaciones (groupby, resample, merge) con pandas sobre subset. | BDG2 subset | Tiempos | 1 | I | ready | Tiempos registrados. |
| 3 | `03_benchmark_spark.ipynb` | Mismas ops con pyspark; si no hay Spark, fallback a `dask`. | BDG2 subset | Tiempos | 2 | A | external | Resultado idéntico. |
| 4 | `04_comparativa_resultados.ipynb` | Plots speedup, cuándo merece la pena Spark, regla de tamaño. | 2+3 | Recomendación | 3 | I | ready | Curva pandas/Spark coherente. |

### `10_case_J_traffic_yolo/`

| # | Notebook | Propósito | Inputs | Outputs | Deps | Nivel | Ejecutable | Validaciones |
|---|---|---|---|---|---|---|---|---|
| 1 | `01_captura_imagenes_dgt.ipynb` | Estrategia captura: cron, retry, almacenamiento MinIO-style. | docs | Diagrama | — | B | ready | — |
| 2 | `02_inferencia_yolo.ipynb` | YOLO (mock por defecto, real con `ultralytics`); conteo + confidence. | imágenes mock | Series | 1 | A | mocked | Output `(count, conf)` válido. |
| 3 | `03_series_temporales_trafico.ipynb` | Ingesta a InfluxDB + queries por cámara y por hora. | 2 | Plata `traffic_cameras` | 2 | I | needs-stack (real) / ready (mock) | Tags correctos. |
| 4 | `04_integracion_meteo_trafico.ipynb` | Cruzar tráfico con AEMET; modelo predicción congestión. | 3 + AEMET mock | Modelo + plots | 3 | A | ready | Correlación lluvia-congestión visible. |

## Datos versus mocks

- **Datos reales esperados:** ninguno requerido para que un alumno pueda
  abrir cualquier notebook y ejecutarlo de extremo a extremo.
- **Mocks:** todos los datasets externos (BDG2, ERA5, In-Gauge, LBNL FDD,
  AEMET) tienen un mock pequeño en `notebooks/_data/` etiquetado claramente
  con encabezado `# MOCK — sintético, no representa datos reales`.
- **Stack levantado:** los notebooks marcados `needs-stack` requieren
  `make demo` para insertar / leer de Influx, pero todos tienen un branch
  fallback que muestra cómo serían los datos.

## Validaciones cruzadas que cada notebook debe ejecutar

- **Schema CAPTIA:** measurement `captia_point`, 5 tags (`captia_env`,
  `domain_id`, `site_id`, `asset_id`, `variable`), field `value` (float).
- **Determinismo:** `seed=42` por defecto; usar `np.random.default_rng`.
- **Rutas relativas:** ningún path absoluto. `pathlib.Path(__file__)` o
  raíz del notebook.
- **Sin secretos:** lectura de `.env` con `python-dotenv`; nunca commitear
  `.env`.
- **Bilingüe coherente:** docs en español, identificadores en inglés
  (excepción: claves del schema CAPTIA).

## Orden recomendado de lectura

1. `00_project_overview/00..02` (45 min — orientación obligatoria).
2. **Caso A** `01..03` (20 min — entender el pipeline real).
3. Caso elegido por equipo (B/C/D/E completos).
4. **Caso F** (MLOps) cuando empiece la fase de modelos.
5. **Caso G** en paralelo desde semana 1.
6. **Caso H** una vez que el equipo tiene un modelo entrenado.
7. **Casos I y J** opcionales / paralelos.

## Roadmap de notebooks

- v1 (este sprint): los 45 notebooks base con mocks, ejecución offline o con
  stack `make demo`.
- v1.1: añadir notebook `06_3_pruebas_carga_datos_reales.ipynb` cuando
  CAPTIA proporcione el dump de InfluxDB.
- v1.2: añadir Caso K si se confirma (test calidad chatbot ya cubierto en
  `07/04` y `08/05`).
