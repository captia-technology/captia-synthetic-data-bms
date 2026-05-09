# Matriz de casos de uso CAPTIA Synthetic Data BMS

> **Última verificación:** 2026-05-10
> **Fuente de verdad:** `docs/archive/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md` ·
> `docs/archive/CENTINELA_Guia_Alumnos_v4.md` ·
> `docs/specs/synthetic-bms/01-product-spec.md`.

Este documento conecta cada caso de uso del Curso de Especialización IA & Big
Data del IES Simarro con su lugar en la **arquitectura Medallion** (bronce →
plata → oro), los datasets y notebooks que lo cubren en este repo, y las
dependencias entre equipos.

## Leyenda de estado

| Estado | Significado |
|--------|-------------|
| `available` | Soportado de extremo a extremo en este repo (notebooks ejecutables + datos sintéticos). |
| `mocked` | Soportado en modo didáctico con mocks; integración con servicios externos pendiente. |
| `external` | Lógicamente cubierto pero apoyado en datasets / herramientas fuera del repo (ERA5, BDG2, MinIO, MLflow…). |

## Casos de uso v1

### Caso A — Pipeline IoT CENTINELA+ (MQTT → Telegraf → InfluxDB)

| Campo | Valor |
|---|---|
| **Objetivo** | Reproducir el flujo completo de CENTINELA+ con sensores reales. |
| **Audiencia** | Profesores, alumnos, equipos nuevos de CAPTIA / centros que se incorporen a la red. |
| **Equipo (curso 2025-26)** | Pendiente de asignación (G2 evalúa migrar a Caso G). |
| **Datasets esperados** | In-Gauge / En-Gage (CSV) o equivalente; opcional: dump CAPTIA. |
| **Capa Bronce** | CSV crudo del dataset público o payload MQTT en bruto. |
| **Capa Plata** | InfluxDB local con `captia_point` + 5 tags + `value`, en buckets `telemetry` / `state_events` / `captia_metadata`. |
| **Capa Oro** | Dashboards Grafana provisionados; queries Flux que consumen capa plata. |
| **Notebooks** | `notebooks/01_case_A_pipeline_iot/01..03_*.ipynb` |
| **Dependencias** | Ninguna (es la base que demuestra cómo se construyen las capas). |
| **Estado** | `available` (stack `make demo` operativo, schema validado en suite 198/198 tests). |
| **Gaps** | H-01 (`ts_ns` vs `ts` ISO en eventos) — decisión arquitectónica con upstream pendiente. |

---

### Caso B — Predicción consumo eléctrico 24h

| Campo | Valor |
|---|---|
| **Objetivo** | Modelos SARIMA / XGBoost / LSTM para forecast de `power_01` con horizonte 24 h. |
| **Audiencia** | Alumnos G1 (Sergio, Ainhoa, Guillermo, Jordi). |
| **Datasets esperados** | BDG2 (educational subset, ~5–10 edificios × 12 meses) + UCI Appliances Energy + `caseB_consumption.yaml` sintético. |
| **Capa Bronce** | `electricity.csv` y `weather.csv` de BDG2; UCI `energydata_complete.csv`. |
| **Capa Plata** | InfluxDB con `power_01`, `temperature_outdoor`, `solar_irradiance`, `occupancy`, `ac_state` (tags `domain_id=bms_buildings`, `site_id=bdg2_education` / `bms_classrooms`, `site_id=ies_simarro`). |
| **Capa Oro** | DataFrame con features temporales (hora, día semana, lag-24h, lag-168h, rolling) + variable objetivo + experimento MLflow. |
| **Notebooks** | `notebooks/02_case_B_energy_forecasting/01..05_*.ipynb` (5 notebooks). |
| **Dependencias** | Subconjunto BDG2 generado en Caso I; meteorología compartida con Caso E; modelo expuesto como tool en Caso H. |
| **Estado** | `available` para ETL bronce→plata + features + baseline; `mocked` para LSTM (Keras opcional). |
| **Gaps** | Calibración real con `simarro-prod` no disponible (sin histórico); usar DC-02 + dump Caso B 12 meses. |

---

### Caso C — Detección de anomalías HVAC

| Campo | Valor |
|---|---|
| **Objetivo** | Isolation Forest + Autoencoder distinguir HVAC normal vs fallo (`valve_stuck`, `sensor_drift`, `fan_failure`, `refrigerant_low`). |
| **Audiencia** | Alumnos G3 (Joan Juan, Edgar, Iván, Joan Benavent). |
| **Datasets esperados** | LBNL FDD ZIP (~6.8 GB) + dataset sintético `caseC_faults.yaml` con etiquetas. |
| **Capa Bronce** | LBNL FDD CSV por subsistema; payload MQTT del generador con `BMS_FAULTS_ENABLED=true`. |
| **Capa Plata** | `temperature_supply`, `temperature_return`, `fan_speed_*`, `valve_*` en `telemetry` / `state_events`. Etiquetas en `captia_fault_labels` (measurement separado, bucket `state_events`, 90 d). |
| **Capa Oro** | Dataset etiquetado (DataFrame con features + columna `is_fault` + `fault_type`) + modelo Isolation Forest entrenado + métricas (precision, recall, AUC). |
| **Notebooks** | `notebooks/03_case_C_hvac_anomaly_detection/01..05_*.ipynb` (5 notebooks). |
| **Dependencias** | `extensions/bms_calibration/FaultInjector` y `FaultEventEmitter` (ADR-010). |
| **Estado** | `available` (suite tests + `tests/integration/test_faults.py` valida 4 tipos). |
| **Gaps** | Caso C live E2E con dump real de CAPTIA aún pendiente (L-PV-02 confirmada cableada). |

---

### Caso D — Calidad de aire, confort interior y ocupación

| Campo | Valor |
|---|---|
| **Objetivo** | Detectar ocupación a partir de variables ambientales (CO₂, T, HR, ruido, lux) sin sensor de presencia. Calcular IAQ. |
| **Audiencia** | Alumnos G4 (Maria, MJ, Federico, Lucia, Jose). |
| **Datasets esperados** | In-Gauge / En-Gage (16 CSV) + UCI Occupancy + `caseD_iaq.yaml` sintético (resolución 1 min). |
| **Capa Bronce** | CSVs originales con `IndoorCO2`, `IndoorTemperature`, `IndoorHumidity`, `Occupied`. |
| **Capa Plata** | `co2`, `temperature_01`, `relative_humidity_01`, `avg_sound_level`, `luminosity`, `iaq_index`, `occupancy` (bool_presence) en `telemetry` (rollup 1m). |
| **Capa Oro** | DataFrame pivotado por timestamp con features + etiqueta `occupancy` (1/0) + clasificador Random Forest. |
| **Notebooks** | `notebooks/04_case_D_iaq_occupancy/01..05_*.ipynb` (5 notebooks). |
| **Dependencias** | Coordina con G3 sobre variables exteriores comunes (T, HR, lux). |
| **Estado** | `available` (caso más alineado con AULA01 real). |
| **Gaps** | Validación contra dataset real de aulas pendiente; usar In-Gauge como referencia. |

---

### Caso E — Meteorología y predicción de generación solar

| Campo | Valor |
|---|---|
| **Objetivo** | ETL ERA5 a `weather_station/xativa/era5_gridpoint` + modelo predicción FV. |
| **Audiencia** | Alumnos G3. |
| **Datasets esperados** | ERA5 NetCDF (ECMWF) y AEMET JSON. |
| **Capa Bronce** | NetCDF crudo en MinIO o filesystem local. |
| **Capa Plata** | `temperature_outdoor` (K → °C), `solar_irradiance` (J/m² → W/m²), `precipitation` (m → mm), `wind_speed` (sqrt(u²+v²)), `pressure` (Pa → hPa), tags `domain_id=weather_station`, `site_id=xativa`, `asset_id=era5_gridpoint`. |
| **Capa Oro** | Modelo de predicción solar (regressor) + curva diaria + tool del chatbot. |
| **Notebooks** | `notebooks/05_case_E_weather_solar/01..04_*.ipynb` (4 notebooks). |
| **Dependencias** | Servirá entrada al Caso B (T_ext) y Caso H (tools). |
| **Estado** | `external` — el repo cubre el contrato de plata e ingesta vía notebook con mocks ERA5; ERA5 real se descarga fuera del repo. |
| **Gaps** | Descarga ERA5 requiere CDS API key del usuario; mock incluido para clase. |

---

### Caso F — MLOps y ciclo de vida de modelos

| Campo | Valor |
|---|---|
| **Objetivo** | MLflow + lakeFS para reproducibilidad de experimentos y datasets. |
| **Audiencia** | Alumnos G4 (transversal). |
| **Datasets** | Sin dataset propio — actúa sobre artefactos de los demás casos. |
| **Capa Bronce/Plata** | N/A — gestiona metadatos, no datos. |
| **Capa Oro** | Convención de naming experiment-name, registry de tags lakeFS sobre el dump 12 meses, ejemplo de tracking. |
| **Notebooks** | `notebooks/06_case_F_mlops/01..03_*.ipynb` (3 notebooks). |
| **Dependencias** | Bloquea / habilita a todos los demás equipos en semana 1. |
| **Estado** | `mocked` — usamos `mlflow.start_run` con backend local SQLite + URIs lakeFS-style; lakeFS server no incluido. |
| **Gaps** | Servidor MLflow + lakeFS no levantado en `docker compose` (decisión: mantener stack ligero v1). |

---

### Caso G — Calidad de datos con agentes especialistas

| Campo | Valor |
|---|---|
| **Objetivo** | Reglas de calidad sobre bronce, plata y oro de todos los equipos + agentes especialistas (Pydantic AI / LangChain). |
| **Audiencia** | Alumnos G2 (Oscar, Vicent, David — pendiente de confirmación) o equivalente. |
| **Datasets** | Datos de los demás equipos (auditoría transversal). |
| **Capa Bronce** | Reglas Great Expectations sobre CSV originales (semana 1, sin dependencias). |
| **Capa Plata** | Reglas Flux sobre InfluxDB: completitud por variable, rango físico, tags presentes, `state_events` no contamina `telemetry`. |
| **Capa Oro** | Balance de clases en datasets supervisados (Caso C, D); auditoría de experimentos MLflow; agente evaluador del chatbot. |
| **Notebooks** | `notebooks/07_case_G_data_quality_agents/01..04_*.ipynb` (4 notebooks). |
| **Dependencias** | Trabaja en oleadas: bronce sem 1, plata sem 2, oro sem 3. |
| **Estado** | `available` — incluye 5 issues reales (`H-1` site_id, `H-2` registry, `H-3` env mix, `#27`, `#29`) como casos de estudio. |
| **Gaps** | Agentes LLM requieren `OPENAI_API_KEY` o Ollama local — en notebook se mockean. |

---

### Caso H — RAG, agentes IA y chatbot

| Campo | Valor |
|---|---|
| **Objetivo** | Chatbot con tools sobre InfluxDB + RAG sobre ElasticSearch que llama a modelos predictivos de Casos B/C/E. |
| **Audiencia** | Alumnos G1. |
| **Datasets** | Datos de InfluxDB (capa plata) + documentos para RAG (normativa OMS, CENTINELA+, datasets). |
| **Capa Bronce** | Documentos en `notebooks/_data/docs_rag_seed/` (markdown). |
| **Capa Plata** | InfluxDB plata (consumida por tools, no producida por este equipo). |
| **Capa Oro** | Tools `query_influxdb`, `compare_periods`, `get_weather_prediction`, `get_consumption_prediction`, `get_building_state`, `check_hvac_anomaly` + índice ElasticSearch + golden set evaluado. |
| **Notebooks** | `notebooks/08_case_H_rag_chatbot/01..05_*.ipynb` (5 notebooks). |
| **Dependencias** | Usa modelos B (propio), E (G3) y C (G3). En semanas 1–2 todos mockeables. |
| **Estado** | `mocked` — arquitectura completa con mocks; cambio a producción en semana 3 es 1-line swap. |
| **Gaps** | LLM y ElasticSearch no incluidos en stack; documento detalla integración. |

---

### Caso I — Big Data: benchmark Spark vs pandas

| Campo | Valor |
|---|---|
| **Objetivo** | Demostrar empíricamente ventajas de Spark frente a pandas con BDG2 (53M+ filas). |
| **Audiencia** | Alumnos G2. |
| **Datasets** | BDG2 completo (ZIP de Kaggle / Zenodo). |
| **Capa Bronce** | CSV BDG2 (electricity, water, gas, weather, metadata). |
| **Capa Plata** | Subconjunto educacional (5–10 edificios × 12 meses) cargado en InfluxDB plata para Caso B. |
| **Capa Oro** | Notebook comparativo: tiempos pandas vs Spark, gráficas escalado, criterios de cuándo usar cada uno. |
| **Notebooks** | `notebooks/09_case_I_spark_vs_pandas/01..04_*.ipynb` (4 notebooks). |
| **Dependencias** | El subconjunto se entrega a G1 (Caso B). |
| **Estado** | `external` — pyspark no es dependencia obligatoria del repo; notebook funciona también con `pandas + dask` como fallback. |
| **Gaps** | Cluster Hadoop ITI fuera del repo; benchmark se ejecuta en local (sample reducido) y se documenta cómo extrapolar. |

---

### Caso J — Tráfico y visión artificial YOLOv

| Campo | Valor |
|---|---|
| **Objetivo** | Captura periódica imágenes DGT, inferencia YOLO, serie temporal de conteo de vehículos correlacionada con meteorología. |
| **Audiencia** | Alumno G5 (Jorge, trabajo en remoto desde Galicia). |
| **Datasets** | JPEG cámaras DGT + AEMET JSON. |
| **Capa Bronce** | Imágenes JPEG en MinIO (`cameras/{camera_id}/{date}/{ts}.jpg`). |
| **Capa Plata** | `vehicle_count`, `congestion_level`, `detection_confidence` en InfluxDB con `domain_id=traffic_cameras`, `site_id=valencia`, `asset_id=DGT_CAM_*`. |
| **Capa Oro** | Serie + features meteorológicos → modelo predicción congestión (XGBoost / RF). |
| **Notebooks** | `notebooks/10_case_J_traffic_yolo/01..04_*.ipynb` (4 notebooks). |
| **Dependencias** | Requiere `ultralytics` (YOLOv8) — opcional, mock incluido. |
| **Estado** | `mocked` — pipeline completo demostrado con imágenes sintéticas y conteos simulados; conexión DGT real fuera del repo. |
| **Gaps** | Cámaras DGT activas dependen del entorno; cron job de captura documentado. |

---

### Caso extra — Test de calidad / evaluación de chatbot con agentes

| Campo | Valor |
|---|---|
| **Objetivo** | Agente evaluador automatizado del chatbot del Caso H: golden set de preguntas + scoring (relevancia, coherencia, hallucination). |
| **Audiencia** | Alumnos G4 (caso nuevo) — sinergia con G1. |
| **Datasets** | Golden set propio (`notebooks/_data/chatbot_golden_set.csv`). |
| **Capa Bronce** | CSV con `question`, `expected_answer`, `category`. |
| **Capa Plata** | Mismo CSV, normalizado y versionado. |
| **Capa Oro** | Score por respuesta + agregados por categoría + matriz de confusión semántica. |
| **Notebooks** | Cubierto en `notebooks/07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb` y `notebooks/08_case_H_rag_chatbot/05_evaluacion_chatbot.ipynb`. |
| **Estado** | `mocked` — implementado como heurística + comparación semántica con embeddings simulados. |
| **Gaps** | Mismos que Caso H (LLM externo). |

## Tabla resumen

| Caso | Equipo | Bronce | Plata (Influx) | Oro | Notebooks | Estado |
|---|---|---|---|---|---|---|
| A | (pendiente) | CSV In-Gauge | `telemetry` + `state_events` | dashboards | 3 | available |
| B | G1 | BDG2 + UCI | `bms_buildings` + `bms_classrooms` | features + modelo | 5 | available |
| C | G3 | LBNL FDD + sintético | `state_events` + `captia_fault_labels` | dataset etiquetado + IF/AE | 5 | available |
| D | G4 | In-Gauge + UCI Occ | `bms_classrooms` 1m | dataset pivot + RF | 5 | available |
| E | G3 | ERA5 + AEMET | `weather_station` | predictor solar | 4 | external |
| F | G4 | n/a | n/a | tracking + lakeFS | 3 | mocked |
| G | G2/G4 | reglas sobre bronce | reglas sobre plata | agentes calidad | 4 | available |
| H | G1 | docs + InfluxDB | (consumidor) | tools + RAG | 5 | mocked |
| I | G2 | BDG2 completo | subset → Caso B | benchmark | 4 | external |
| J | G5 | JPEG + AEMET | `traffic_cameras` | predicción congestión | 4 | mocked |
| Extra | G4 | golden set | dataset normalizado | scoring chatbot | (compartido G+H) | mocked |

**Total notebooks:** 3 (overview) + 3+5+5+5+4+3+4+5+4+4 = 45 notebooks didácticos.

## Decisiones tomadas frente a contradicciones de las fuentes

1. **Naming de variables (alias guion vs underscore).** La guía CENTINELA+
   mezcla `temperature-indoor` (línea 416) y `temperature_01` (línea 59).
   Este repo normaliza **todo a underscore** para evitar quoting Flux. Tabla
   de equivalencias en `docs/specs/synthetic-bms/02-domain-spec.md:122-140`.
2. **Catálogo de variables.** La guía habla de `captia_metadata`. La PPTX
   simarro-prod usa `captia_point_meta` dentro del bucket `captia_metadata`.
   Este repo adopta la **versión PPTX** (`captia_point_meta`).
3. **Etiquetado de fallos Caso C.** Se materializan en `captia_fault_labels`
   (measurement separado, bucket `state_events`), no en `captia_point`.
4. **Bucket count.** La guía menciona "9 buckets". El repo expone **7
   buckets** (`telemetry`, `_1m`, `_15m`, `_1h`, `state_events`,
   `telemetry_events`, `captia_metadata`). Diferencia: el repo no separa
   `events_*` ni mantiene `metadata_legacy`. Documentado en
   `docs/audit/CONSISTENCY_MATRIX.md`.
5. **Asignación Caso A.** En la guía se señala como pendiente. Este repo
   provee el código de referencia ya operativo, independientemente de la
   asignación final del curso.
6. **Caso F (MLOps).** No está en `Non-goals` v1 del product spec — incluido
   como notebook documental sin levantar servidor MLflow.

## Trazabilidad

Cada notebook lleva una línea
`> _Caso de uso: X · Capa Medallion: Y · Spec: docs/specs/.../...md_` en su
celda inicial para que la inspección visual permita reconstruir el mapa.
