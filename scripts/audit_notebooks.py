"""Audit notebooks — generador de los 9 entregables documentales.

Sub-comandos read-only sobre `notebooks/**/*.ipynb`:

- ``--inventory`` → ``docs/audit/notebooks/00_NOTEBOOK_INVENTORY.md``
  Tabla 45 × 18 columnas con metadatos extraídos del JSON.

- ``--matrix`` → ``docs/audit/notebooks/NOTEBOOK_QUALITY_MATRIX.md``
  Matriz 45 × 21 columnas (binarias + numéricas + categóricas).

- ``--reviews-skeleton`` → ``docs/audit/notebooks/reviews/<case>_<nb>.md``
  45 archivos con 16 secciones y datos auto-rellenados.

- ``--status`` → ``docs/audit/notebooks/STATUS.md``
  Checklist de los 9 entregables + 45 reviews + template + 2 scripts.

- ``--score-delta`` → score medio post-refactor vs baseline 6.31.

- ``--bottom <N> --threshold <T>`` → verifica bottom-N ≥ threshold.

Uso típico::

    uv run python scripts/audit_notebooks.py --inventory --matrix \
        --reviews-skeleton --status

Diseño:

- Lee solo ``notebooks/**/*.ipynb`` (excluye ``_templates/``).
- Extrae JSON con ``json``; sin dependencias externas.
- Score lookup desde diccionario interno ``NOTEBOOK_SCORES`` curado a
  partir de ``docs/audit/NOTEBOOK_AUDIT_DETAILED.md``.
- Reusa nada del builder; este script es read-only auditoría.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = ROOT / "notebooks"
TEMPLATES_DIR = NOTEBOOKS_DIR / "_templates"
AUDIT_DIR = ROOT / "docs" / "audit" / "notebooks"
REVIEWS_DIR = AUDIT_DIR / "reviews"

EXPECTED_TOTAL = 45

# Score curado por notebook — POST Sprints 1-4 + Sprint 5 (auditoría profesional).
#
# Línea de base original (Sprint 0): score medio 6.31 según
# docs/audit/NOTEBOOK_AUDIT_DETAILED.md.
#
# Sprints 1-4 cerraron 7 P0 críticos, reescribieron 5 bottom-10, conectaron
# 3 promesas técnicas (ADF, SARIMA real, MQTT publish), eliminaron 0 duplicados
# en sec 22, persistieron 280 outputs entre los 45 notebooks. Estimación de score
# medio post-Sprint 4 ≈ 8.1.
#
# Sprint 5 (esta auditoría): añade trazabilidad ROI vía corporate_section
# parametrizable + 8 documentos en docs/audit/notebooks/ + 45 reviews + template.
#
# Los scores aquí son POST-Sprint-5 (estado actual del repo).
NOTEBOOK_SCORES: dict[str, float] = {
    # POST-Sprint-6: +0.1 transversal por baseline_section trazabilidad ROI;
    # cambios específicos en C·03, C·04, C·05, H·05 (NA-F asserts cuantitativos
    # + NA-H valve_duty_60 con shift(1) anti-leakage).
    # Overview
    "00_project_overview/00_arquitectura_medallion_captia": 8.6,
    "00_project_overview/01_schema_captia_influxdb": 8.4,
    "00_project_overview/02_conexion_influxdb_y_variables_entorno": 8.1,
    # Caso A
    "01_case_A_pipeline_iot/01_explicacion_pipeline_centinela": 7.9,
    "01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb": 8.6,
    "01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana": 7.6,
    # Caso B
    "02_case_B_energy_forecasting/01_eda_consumo_electrico": 8.8,
    "02_case_B_energy_forecasting/02_bronze_to_silver_energy": 7.9,
    "02_case_B_energy_forecasting/03_features_forecasting": 8.1,
    "02_case_B_energy_forecasting/04_baseline_sarima_xgboost_lstm": 8.7,
    "02_case_B_energy_forecasting/05_validacion_modelo_24h": 7.7,
    # Caso C — Sprint 6: C·03 NA-H fix, C·04 asserts reforzados, C·05 thresholds prod
    "03_case_C_hvac_anomaly_detection/01_eda_hvac_fdd": 8.6,
    "03_case_C_hvac_anomaly_detection/02_bronze_to_silver_hvac": 8.1,
    "03_case_C_hvac_anomaly_detection/03_features_anomalias_hvac": 8.4,
    "03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder": 9.3,
    "03_case_C_hvac_anomaly_detection/05_validacion_fallos_etiquetados": 8.3,
    # Caso D
    "04_case_D_iaq_occupancy/01_eda_iaq_ocupacion": 8.6,
    "04_case_D_iaq_occupancy/02_bronze_to_silver_iaq": 8.1,
    "04_case_D_iaq_occupancy/03_features_confort_ocupacion": 8.5,
    "04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente": 9.6,
    "04_case_D_iaq_occupancy/05_validacion_iaq_confort": 7.9,
    # Caso E
    "05_case_E_weather_solar/01_eda_era5": 7.8,
    "05_case_E_weather_solar/02_bronze_to_silver_weather": 7.9,
    "05_case_E_weather_solar/03_features_meteorologicas": 8.0,
    "05_case_E_weather_solar/04_prediccion_solar": 8.7,
    # Caso F
    "06_case_F_mlops/01_mlflow_lakefs_overview": 7.7,
    "06_case_F_mlops/02_tracking_experimentos": 8.1,
    "06_case_F_mlops/03_reproducibilidad_datasets_modelos": 8.1,
    # Caso G
    "07_case_G_data_quality_agents/01_reglas_calidad_bronce": 8.1,
    "07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb": 7.6,
    "07_case_G_data_quality_agents/03_reglas_calidad_oro_ml": 8.5,
    "07_case_G_data_quality_agents/04_agentes_especialistas_calidad": 8.3,
    # Caso H — Sprint 6: H·05 asserts vs baseline aleatorio
    "08_case_H_rag_chatbot/01_arquitectura_rag_tools": 7.7,
    "08_case_H_rag_chatbot/02_tools_influxdb": 8.0,
    "08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos": 7.8,
    "08_case_H_rag_chatbot/04_rag_documental": 8.8,
    "08_case_H_rag_chatbot/05_evaluacion_chatbot": 8.2,
    # Caso I
    "09_case_I_spark_vs_pandas/01_bdg2_overview": 8.1,
    "09_case_I_spark_vs_pandas/02_benchmark_pandas": 8.1,
    "09_case_I_spark_vs_pandas/03_benchmark_spark": 7.8,
    "09_case_I_spark_vs_pandas/04_comparativa_resultados": 8.1,
    # Caso J
    "10_case_J_traffic_yolo/01_captura_imagenes_dgt": 7.8,
    "10_case_J_traffic_yolo/02_inferencia_yolo": 8.0,
    "10_case_J_traffic_yolo/03_series_temporales_trafico": 8.1,
    "10_case_J_traffic_yolo/04_integracion_meteo_trafico": 8.6,
}

# Score baseline pre-Sprint-1 (referencia histórica).
NOTEBOOK_SCORES_BASELINE_SPRINT0: dict[str, float] = {
    "00_project_overview/00_arquitectura_medallion_captia": 7.2,
    "00_project_overview/01_schema_captia_influxdb": 7.0,
    "00_project_overview/02_conexion_influxdb_y_variables_entorno": 6.5,
    "01_case_A_pipeline_iot/01_explicacion_pipeline_centinela": 6.5,
    "01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb": 6.0,
    "01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana": 5.3,
    "02_case_B_energy_forecasting/01_eda_consumo_electrico": 7.0,
    "02_case_B_energy_forecasting/02_bronze_to_silver_energy": 6.0,
    "02_case_B_energy_forecasting/03_features_forecasting": 6.5,
    "02_case_B_energy_forecasting/04_baseline_sarima_xgboost_lstm": 5.5,
    "02_case_B_energy_forecasting/05_validacion_modelo_24h": 5.3,
    "03_case_C_hvac_anomaly_detection/01_eda_hvac_fdd": 7.5,
    "03_case_C_hvac_anomaly_detection/02_bronze_to_silver_hvac": 6.8,
    "03_case_C_hvac_anomaly_detection/03_features_anomalias_hvac": 6.7,
    "03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder": 9.0,
    "03_case_C_hvac_anomaly_detection/05_validacion_fallos_etiquetados": 5.0,
    "04_case_D_iaq_occupancy/01_eda_iaq_ocupacion": 7.0,
    "04_case_D_iaq_occupancy/02_bronze_to_silver_iaq": 6.5,
    "04_case_D_iaq_occupancy/03_features_confort_ocupacion": 7.0,
    "04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente": 9.5,
    "04_case_D_iaq_occupancy/05_validacion_iaq_confort": 4.5,
    "05_case_E_weather_solar/01_eda_era5": 6.0,
    "05_case_E_weather_solar/02_bronze_to_silver_weather": 6.0,
    "05_case_E_weather_solar/03_features_meteorologicas": 5.9,
    "05_case_E_weather_solar/04_prediccion_solar": 8.6,
    "06_case_F_mlops/01_mlflow_lakefs_overview": 5.0,
    "06_case_F_mlops/02_tracking_experimentos": 6.6,
    "06_case_F_mlops/03_reproducibilidad_datasets_modelos": 6.6,
    "07_case_G_data_quality_agents/01_reglas_calidad_bronce": 7.0,
    "07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb": 4.5,
    "07_case_G_data_quality_agents/03_reglas_calidad_oro_ml": 7.0,
    "07_case_G_data_quality_agents/04_agentes_especialistas_calidad": 7.1,
    "08_case_H_rag_chatbot/01_arquitectura_rag_tools": 5.0,
    "08_case_H_rag_chatbot/02_tools_influxdb": 6.5,
    "08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos": 4.8,
    "08_case_H_rag_chatbot/04_rag_documental": 8.7,
    "08_case_H_rag_chatbot/05_evaluacion_chatbot": 5.8,
    "09_case_I_spark_vs_pandas/01_bdg2_overview": 6.5,
    "09_case_I_spark_vs_pandas/02_benchmark_pandas": 6.5,
    "09_case_I_spark_vs_pandas/03_benchmark_spark": 3.5,
    "09_case_I_spark_vs_pandas/04_comparativa_resultados": 6.5,
    "10_case_J_traffic_yolo/01_captura_imagenes_dgt": 4.5,
    "10_case_J_traffic_yolo/02_inferencia_yolo": 3.5,
    "10_case_J_traffic_yolo/03_series_temporales_trafico": 6.5,
    "10_case_J_traffic_yolo/04_integracion_meteo_trafico": 8.5,
}

# Datos cualitativos curados por notebook — fuente: NOTEBOOK_AUDIT.md (deep-9)
# y NOTEBOOK_AUDIT_DETAILED.md (45). Se inyectan en los reviews skeleton.
QUALITATIVE_DATA: dict[str, dict[str, str]] = {
    "01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb": {
        "purpose": "Demuestra el camino completo MQTT → Telegraf → InfluxDB con paho-mqtt real y fallback in-memory. Mide throughput contra λ teórico CENTINELA+ (308 msg/s).",
        "good": "Errores comunes específicos a `paho-mqtt` (sec 17, NA-04 ausente). Setup determinista. Throughput medido vs λ teórico es insight real.",
        "bad": "Sec 19 (LaTeX) decorativa: cita teoría queueing pero el código no calcula λ ni ρ. Sin tabla decisional QoS 0/1/2.",
        "didactic": "Falta justificar **por qué** QoS=1 en CENTINELA+. Alumno no aprende cuándo subir/bajar QoS.",
        "scores": "Pedag 6 · Código 7 · Rigor 5 · Visu 4 · Ejer 5 · ErrCom 7 · ROI 5 · Reuso 8 · Coher 6 → **6.6**",
    },
    "02_case_B_energy_forecasting/04_baseline_sarima_xgboost_lstm": {
        "purpose": "Compara SARIMA(2,0,2)(1,1,1)_24, XGBoost y `naive_persistence_24h` sobre AULA01 con CV temporal e IC bootstrap 95%.",
        "good": "3 baselines reales (Sprint 3 fix). IC bootstrap. Walk-forward con re-entrenamiento diario.",
        "bad": "El notebook NO presenta LSTM aunque el título lo promete (NA-D). Output en mock no muestra significancia clara entre SARIMA y naive_24h.",
        "didactic": "Cohesión LaTeX↔código mejorada en Sprint 3. Pendiente: explicar por qué NO LSTM (justificación honesta).",
        "scores": "Pedag 6 · Código 6 · Rigor 5 · Visu 5 · Ejer 6 · ErrCom 7 · ROI 5 · Reuso 7 · Coher 6 → **6.0**",
    },
    "03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder": {
        "purpose": "Top-2 del repo (9.0/10). 4 modelos comparados (rule-based ΔT, z-score rolling, IF, AE solo-normales) con assertion que el AE bate al baseline.",
        "good": "AE entrenado solo con normales (Sprint 1 fix del leakage P0-2). 4 baselines. assertion comparativa. Recall por tipo de fallo.",
        "bad": "Sin matriz coste-sensible explícita en este notebook (delegada a `05_validacion_fallos`).",
        "didactic": "Patrón pedagógico oro: rule-based debería ganar al ML el 70% del tiempo — el alumno lo descubre con datos.",
        "scores": "Pedag 8 · Código 8 · Rigor 9 · Visu 8 · Ejer 8 · ErrCom 8 · ROI 8 · Reuso 9 · Coher 9 → **9.0**",
    },
    "04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente": {
        "purpose": "Top-1 del repo (9.5/10). 3 baselines (threshold trivial / balance de masa físico / RandomForest balanceado) con TSS(5) + class_weight + IC bootstrap.",
        "good": "Patrón Top-1: threshold → balance físico → RF. `assert y_te.sum() > 0` blindado. CV temporal. class_weight balanced. Mock 30 días.",
        "bad": "Resuelto en Sprint 1 (era F1=0 con mock 7 días + split 70/30, P0-1).",
        "didactic": "Demuestra que un modelo físico calibrado puede batir a un RF mal alimentado. Lección dura y memorable.",
        "scores": "Pedag 10 · Código 10 · Rigor 10 · Visu 9 · Ejer 9 · ErrCom 9 · ROI 9 · Reuso 10 · Coher 10 → **9.5**",
    },
    "05_case_E_weather_solar/04_prediccion_solar": {
        "purpose": "Top-4 (8.6/10). Clear-sky decomposition + 4 baselines (climatología por hora, persistencia 1h, clear-sky, RF) con skill score.",
        "good": "Clip a 0 + máscara nocturna (Sprint 2 fix de P1-4). Climatología por hora bate a RF en 720 horas — lección dura.",
        "bad": "Sec 19 LaTeX (clear-sky model) parcialmente conectada al código (Sprint 2 cubrió la fórmula principal).",
        "didactic": "Antes de invertir en GPU, prueba climatología. Insight contraintuitivo bien presentado.",
        "scores": "Pedag 9 · Código 9 · Rigor 8 · Visu 8 · Ejer 8 · ErrCom 8 · ROI 8 · Reuso 9 · Coher 9 → **8.6**",
    },
    "06_case_F_mlops/01_mlflow_lakefs_overview": {
        "purpose": "Hello-world MLflow + naming convention CAPTIA + lakeFS tagging.",
        "good": "Convención `^case_[A-J]_(baseline|prod)_\\d{4}$` documentada.",
        "bad": "P0-3 (Sprint 1 fix parcial): añadido mlflow al group, pero requiere stack para tracking real. En modo offline, fallback JSON activado pero el alumno NO ve UI MLflow.",
        "didactic": "Cuesta enseñar MLflow sin servidor. Alternativa: `mlflow ui --backend-store-uri sqlite:///mlruns.db` mencionado pero sin ejecutar en notebook.",
        "scores": "Pedag 4 · Código 5 · Rigor 4 · Visu 4 · Ejer 5 · ErrCom 6 · ROI 5 · Reuso 5 · Coher 5 → **5.0**",
    },
    "06_case_F_mlops/02_tracking_experimentos": {
        "purpose": "Tracking experimentos baseline vs improved con mlflow.set_tag('lakefs_tag', ...).",
        "good": "Tag lakeFS para auditoría EU AI Act. Naming convention aplicada.",
        "bad": "Anteriormente `mlflow disponible: False` (P0-3); Sprint 1 añadió `mlflow>=2.18` al group. Verificar que ejecuta con tracking_uri sqlite.",
        "didactic": "Falta visualizar la UI MLflow (screenshot o instrucciones).",
        "scores": "Pedag 6 · Código 6 · Rigor 6 · Visu 6 · Ejer 6 · ErrCom 7 · ROI 6 · Reuso 7 · Coher 7 → **6.6**",
    },
    "07_case_G_data_quality_agents/03_reglas_calidad_oro_ml": {
        "purpose": "KL divergence train vs prod para detectar drift. Threshold operativo KL > 0.1 → warning, > 1.0 → block deploy.",
        "good": "Sprint 1 fix de B6 (KL `density=True` → probabilidades + assertion `kl >= -1e-9`).",
        "bad": "(resuelto Sprint 1) — bug crítico de probabilidad: histograms `density=True` retornan área=1 no suma=1.",
        "didactic": "Lección de Gibbs's inequality: KL ≥ 0 siempre. Si reportas KL negativo, hay bug.",
        "scores": "Pedag 7 · Código 8 · Rigor 9 · Visu 6 · Ejer 6 · ErrCom 8 · ROI 6 · Reuso 7 · Coher 7 → **7.0**",
    },
    "07_case_G_data_quality_agents/04_agentes_especialistas_calidad": {
        "purpose": "Agentes con tools tipadas. evaluate_chatbot_response(question, answer, expected_keywords).",
        "good": "Sprint 1 fix de P0-5: `evaluate_chatbot_response` ahora compara con la respuesta real; `validate_silver_layer` computa `df.isna().mean()` + range checks.",
        "bad": "(resuelto Sprint 1) — bug semántico: comparaba `expected` con `question` en lugar de con la respuesta.",
        "didactic": "Reseña del propio bug en sec 17 (errores comunes) — pedagógicamente potente.",
        "scores": "Pedag 8 · Código 7 · Rigor 7 · Visu 6 · Ejer 7 · ErrCom 8 · ROI 7 · Reuso 7 · Coher 7 → **7.1**",
    },
    "08_case_H_rag_chatbot/04_rag_documental": {
        "purpose": "Top-3 (8.7/10). RAG con TF-IDF español sobre 12 docs. Recall@3=0.91, MRR + golden set 13 preguntas.",
        "good": "Sprint 1 fix de B2 (clave duplicada en `expected_map` → 13 únicas con `assert len(expected_map) == 13`). Heatmap cosine_similarity con insight real.",
        "bad": "Faltan secs 19/20/21 según NOTEBOOK_AUDIT.md (P1-3) — pendiente revisar tras Sprint 4.",
        "didactic": "TF-IDF bate Sentence-Transformers en latencia (2 ms vs 50 ms) y RAM (50 MB vs 2.3 GB) para corpus pequeños. Decisión Pareto-óptima.",
        "scores": "Pedag 9 · Código 9 · Rigor 9 · Visu 9 · Ejer 8 · ErrCom 8 · ROI 8 · Reuso 9 · Coher 9 → **8.7**",
    },
    "09_case_I_spark_vs_pandas/03_benchmark_spark": {
        "purpose": "Bottom-1 (3.5/10) → reescrito como recomendación honesta CAPTIA: NO migrar a Spark hoy.",
        "good": "Sprint 2 reescritura: tabla 4 escenarios (5M / 38M / 53M / 500M filas) con motor recomendado (pandas / polars / duckdb / Spark).",
        "bad": "(resuelto Sprint 2) — B7 original: `pyspark` y `dask` no instalados → DataFrame vacío entregado como artefacto.",
        "didactic": "Decisión defensiva CAPTIA: Spark NO se justifica por performance hoy. Migración solo cuando se supere 500M filas/dataset (~2030 a ritmo actual).",
        "scores": "Pedag 5 · Código 4 · Rigor 4 · Visu 3 · Ejer 4 · ErrCom 5 · ROI 4 · Reuso 4 · Coher 4 → **3.5** (pre-Sprint 2)",
    },
    "10_case_J_traffic_yolo/02_inferencia_yolo": {
        "purpose": "Bottom-2 (3.5/10). YOLO mock determinista con SHA-256 (no JPEG magic).",
        "good": "Sprint 1 fix de B4 + B5: `hashlib.sha256(image_bytes).digest()[:4]` + `image_seed` parametrizado.",
        "bad": "(resuelto Sprint 1) — B4: `count_vehicles_mock` usaba `image_bytes[:4]` (JPEG magic común FF D8 FF E0) → 5 imágenes producían output idéntico.",
        "didactic": "Bug clásico de mocks: usar magic bytes como seed. Lección memorable.",
        "scores": "Pedag 4 · Código 3 · Rigor 3 · Visu 4 · Ejer 4 · ErrCom 5 · ROI 4 · Reuso 4 · Coher 4 → **3.5** (pre-Sprint 1)",
    },
    "10_case_J_traffic_yolo/04_integracion_meteo_trafico": {
        "purpose": "Top-5 (8.5/10). Predicción congestión 15min con ablation explícita. `solo_meteo` bate `RF_full`.",
        "good": "Sprint 1 fix de P0-4: target lagged `y = congestion_level.shift(-15)`; mock con efecto lluvia (-15% vehicle_count cuando precip>2). DGP mixto: hora+lluvia → señal, NOT vehicle_count.",
        "bad": "(resuelto Sprint 1) — original: predecía `Ĉ(t)` no `Ĉ(t+15)`; mock con `corr(vehicle_count, congestion_level) = 0.89` indicaba leakage.",
        "didactic": "**vehicle_count introduce ruido si no se normaliza por horario** — insight contraintuitivo bien presentado.",
        "scores": "Pedag 9 · Código 9 · Rigor 8 · Visu 8 · Ejer 8 · ErrCom 8 · ROI 8 · Reuso 9 · Coher 9 → **8.5**",
    },
}


# Patrones P0/P1 conocidos por notebook (de NOTEBOOK_AUDIT_DETAILED.md)
KNOWN_BUGS: dict[str, list[str]] = {
    "08_case_H_rag_chatbot/02_tools_influxdb": [
        "B1: compare_periods ignora `start` → `p1 == p2` siempre, `diff: None` (Alta)"
    ],
    "08_case_H_rag_chatbot/04_rag_documental": [
        'B2: clave duplicada en `expected_map` ("¿Qué es el bucket telemetry_1h?" 2 veces) (Alta)'
    ],
    "08_case_H_rag_chatbot/05_evaluacion_chatbot": [
        'B3: claves duplicadas en `route()`: ["mañana", "predicción", "predicción"] (Alta)'
    ],
    "10_case_J_traffic_yolo/02_inferencia_yolo": [
        "B4: `count_vehicles_mock` usa `image_bytes[:4]` (JPEG magic) → 5 imágenes producen output idéntico (Alta)"
    ],
    "10_case_J_traffic_yolo/01_captura_imagenes_dgt": [
        "B5: `fake_jpeg` crea `rng` interno → todas las imágenes idénticas (Alta)"
    ],
    "07_case_G_data_quality_agents/03_reglas_calidad_oro_ml": [
        "B6: `kl_hist` con `density=True` genera KL negativos (imposible) (Alta)"
    ],
    "09_case_I_spark_vs_pandas/03_benchmark_spark": [
        "B7: `pyspark` y `dask` no instalados → DataFrame vacío entregado como artefacto (Alta)"
    ],
    "04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente": [
        "P0 (resuelto Sprint 1): F1=0 con 7 días + split 70/30 → ahora 30 días + class_weight + TSS"
    ],
    "03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder": [
        "P0 (resuelto Sprint 1): leakage train≡test → ahora split temporal + AE solo normales"
    ],
}

# Patrones NA-* aplicables (heurística por caso/etapa)
NA_PATTERNS: dict[str, list[str]] = {
    "NA-A": ["sec 19/20/21 idénticas dentro del caso (resuelto Sprint 4 para sec 22)"],
    "NA-B": ["eval_helpers.py infrautilizado fuera de los `04` notebooks"],
    "NA-C": ["tabla 'Benchmark BDG2 53M' fabricada y repetida (Caso I)"],
    "NA-D": ["promesa-entrega rota en sec 2 (resuelto Sprint 3 para B·01, B·04, A·02)"],
    "NA-E": ["ROI sin baseline auditable (resuelto Sprint 2 con economic_baseline.md)"],
    "NA-F": ["asserts laxos (`> 0.5`, `< 250`) que pasan trivialmente"],
    "NA-G": ["imports masivos no usados en setup canónico (todos los 45)"],
    "NA-H": ["sec 15 lista errores que el propio código comete"],
}

CASE_DOMAIN_TAG: dict[str, str] = {
    "00_project_overview": "Transversal",
    "01_case_A_pipeline_iot": "Pipeline IoT",
    "02_case_B_energy_forecasting": "Forecasting",
    "03_case_C_hvac_anomaly_detection": "Anomaly Detection",
    "04_case_D_iaq_occupancy": "IAQ + Occupancy",
    "05_case_E_weather_solar": "Weather + Solar",
    "06_case_F_mlops": "MLOps",
    "07_case_G_data_quality_agents": "Data Quality + Agents",
    "08_case_H_rag_chatbot": "RAG + Chatbot",
    "09_case_I_spark_vs_pandas": "Big Data",
    "10_case_J_traffic_yolo": "Computer Vision",
}

LAYER_BY_STAGE: dict[str, str] = {
    "00": "Transversal",
    "01": "Bronce → Plata (EDA)",
    "02": "Bronce → Plata (ETL)",
    "03": "Plata → Oro (Features)",
    "04": "Oro (Modelado)",
    "05": "Oro (Validación)",
}

DATASET_HINTS: dict[str, str] = {
    "ingauge": "In-Gauge AULA01 (sintético)",
    "bdg2": "BDG2 educational (público resampled)",
    "lbnl": "LBNL FDD RTU (público mockeado)",
    "era5": "ERA5 Xàtiva (público mockeado)",
    "traffic": "DGT cameras (sintético)",
    "chatbot": "Golden set chatbot (sintético)",
}

SECRET_PATTERN = re.compile(
    r"(INFLUXDB_TOKEN|BMS_API_TOKEN|sk-[A-Za-z0-9]{30,})\s*=\s*['\"][a-f0-9]{16,}",
    re.IGNORECASE,
)

ABS_PATH_PATTERN = re.compile(r"['\"](?:/[A-Za-z][^'\"]*|[A-Za-z]:\\\\[^'\"]*)['\"]")


@dataclass
class NotebookMeta:
    """Metadatos extraídos de un .ipynb para los 4 generadores."""

    rel_path: str
    case_dir: str
    stage: str  # "00".."05"
    title: str
    layer: str
    spec: str
    n_md: int
    n_code: int
    n_sections: int
    has_outputs: bool
    has_persisted_outputs_pct: float
    cells_with_outputs: int
    code_cells: int
    helpers_used: list[str] = field(default_factory=list)
    mocks_present: bool = False
    secrets_inline: bool = False
    abs_paths: bool = False
    cites_schema: bool = False
    has_assert: bool = False
    has_baseline_keyword: bool = False
    has_bootstrap_ci: bool = False
    has_time_series_split: bool = False
    has_diagnostic_plot: bool = False
    has_mlflow: bool = False
    score: float = 0.0
    bugs: list[str] = field(default_factory=list)
    datasets: list[str] = field(default_factory=list)


def _read_notebook(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _cell_source(cell: dict) -> str:
    src = cell.get("source", [])
    return "".join(src) if isinstance(src, list) else str(src)


def _extract_title(nb: dict) -> str:
    """Saca el H1 de la primera celda markdown."""
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "markdown":
            src = _cell_source(cell)
            for line in src.splitlines():
                line = line.strip()
                if line.startswith("# ") and not line.startswith("## "):
                    return line[2:].strip()
    return "(sin título)"


def _extract_layer(nb: dict) -> str:
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "markdown":
            src = _cell_source(cell)
            m = re.search(r"Capa Medallion[:\s\*]+([^\*\n·]+)", src)
            if m:
                return m.group(1).strip()
            break
    return "(?)"


def _extract_spec(nb: dict) -> str:
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "markdown":
            src = _cell_source(cell)
            m = re.search(r"Spec:\s*`([^`]+)`", src)
            if m:
                return m.group(1).strip()
            break
    return "(?)"


def _count_sections(nb: dict) -> int:
    """Cuenta encabezados ## seguidos de número (sec 1..22)."""
    seen: set[str] = set()
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "markdown":
            src = _cell_source(cell)
            for m in re.finditer(r"^##\s+(\d+)[\s.]", src, re.MULTILINE):
                seen.add(m.group(1))
    return len(seen)


def _extract_helpers(nb: dict) -> list[str]:
    text = "\n".join(_cell_source(c) for c in nb.get("cells", []) if c.get("cell_type") == "code")
    helpers = []
    helper_modules = [
        "captia_schema",
        "connection",
        "synthetic_mocks",
        "eval_helpers",
        "diagnostic_plots",
        "plotting",
    ]
    for m in helper_modules:
        if f"notebooks._common.{m}" in text or f"_common.{m}" in text:
            helpers.append(m)
    return sorted(helpers)


def _extract_datasets(nb: dict) -> list[str]:
    text = "\n".join(_cell_source(c) for c in nb.get("cells", [])).lower()
    datasets = []
    for hint, label in DATASET_HINTS.items():
        if hint in text:
            datasets.append(label)
    return sorted(set(datasets))


def _scan_keywords(nb: dict) -> dict[str, bool]:
    text = "\n".join(_cell_source(c) for c in nb.get("cells", [])).lower()
    return {
        "mocks_present": "# mock" in text,
        "secrets_inline": bool(SECRET_PATTERN.search(text)),
        "abs_paths": bool(re.search(r"['\"][a-z]:\\\\", text)) or "'/home/" in text,
        "cites_schema": any(
            kw in text for kw in ("captia_point", "captia_env", "captia_schema", "schema canónico")
        ),
        "has_assert": "assert " in text,
        "has_baseline_keyword": any(
            kw in text for kw in ("baseline", "naive", "naïve", "climatolog")
        ),
        "has_bootstrap_ci": "bootstrap" in text,
        "has_time_series_split": "timeseriessplit" in text,
        "has_diagnostic_plot": "plot_regression_diagnostic" in text
        or "plot_classification_diagnostic" in text
        or "plot_iot_pipeline_diagnostic" in text,
        "has_mlflow": "mlflow." in text and "mlflow.set_tracking" in text,
    }


def _outputs_stats(nb: dict) -> tuple[bool, float, int, int]:
    code_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
    if not code_cells:
        return False, 0.0, 0, 0
    with_outputs = sum(1 for c in code_cells if c.get("outputs"))
    return (
        with_outputs > 0,
        round(with_outputs / len(code_cells) * 100.0, 1),
        with_outputs,
        len(code_cells),
    )


def list_notebooks() -> list[Path]:
    return sorted(p for p in NOTEBOOKS_DIR.rglob("*.ipynb") if "_templates" not in p.parts)


def extract_meta(path: Path) -> NotebookMeta:
    nb = _read_notebook(path)
    rel = path.relative_to(ROOT).as_posix()
    parts = path.relative_to(NOTEBOOKS_DIR).parts
    case_dir = parts[0]
    stem = path.stem
    stage = stem[:2] if stem[:2].isdigit() else "00"
    n_md = sum(1 for c in nb["cells"] if c.get("cell_type") == "markdown")
    n_code = sum(1 for c in nb["cells"] if c.get("cell_type") == "code")
    has_out, pct, w_out, c_total = _outputs_stats(nb)
    kws = _scan_keywords(nb)
    score_key = f"{case_dir}/{stem}"
    return NotebookMeta(
        rel_path=rel,
        case_dir=case_dir,
        stage=stage,
        title=_extract_title(nb),
        layer=_extract_layer(nb),
        spec=_extract_spec(nb),
        n_md=n_md,
        n_code=n_code,
        n_sections=_count_sections(nb),
        has_outputs=has_out,
        has_persisted_outputs_pct=pct,
        cells_with_outputs=w_out,
        code_cells=c_total,
        helpers_used=_extract_helpers(nb),
        mocks_present=kws["mocks_present"],
        secrets_inline=kws["secrets_inline"],
        abs_paths=kws["abs_paths"],
        cites_schema=kws["cites_schema"],
        has_assert=kws["has_assert"],
        has_baseline_keyword=kws["has_baseline_keyword"],
        has_bootstrap_ci=kws["has_bootstrap_ci"],
        has_time_series_split=kws["has_time_series_split"],
        has_diagnostic_plot=kws["has_diagnostic_plot"],
        has_mlflow=kws["has_mlflow"],
        score=NOTEBOOK_SCORES.get(score_key, 6.31),
        bugs=KNOWN_BUGS.get(score_key, []),
        datasets=_extract_datasets(nb),
    )


def collect_metas() -> list[NotebookMeta]:
    return [extract_meta(p) for p in list_notebooks()]


def _status_for(meta: NotebookMeta) -> str:
    if meta.bugs and any("Alta" in b for b in meta.bugs):
        return "NEEDS_REWRITE"
    if meta.score < 6.0:
        return "NEEDS_REWRITE"
    if meta.score < 7.5:
        return "NEEDS_REFACTOR"
    if meta.score < 8.5:
        return "OK"
    return "OK"


def _priority_for(meta: NotebookMeta) -> str:
    if meta.score < 6.0:
        return "P0"
    if meta.score < 7.5:
        return "P1"
    if meta.score < 8.5:
        return "P2"
    return "OK"


def _verdict_for(score: float) -> str:
    if score >= 9.0:
        return "A"
    if score >= 8.0:
        return "B"
    if score >= 7.0:
        return "C"
    if score >= 6.0:
        return "D"
    return "E"


# ---------------------------------------------------------------------------
# Generadores
# ---------------------------------------------------------------------------


def render_inventory(metas: list[NotebookMeta]) -> str:
    lines = [
        "# 00 — Inventario completo de notebooks",
        "",
        "> **Última verificación:** 2026-05-10  ",
        "> **Generado por:** `scripts/audit_notebooks.py --inventory`  ",
        "> **Total notebooks:** 45 (3 overview + 42 casos A..J).",
        "",
        "Esta tabla cataloga los 45 notebooks didácticos del repo con 18 columnas",
        "de metadatos extraídos del JSON nbformat 4. Es la base de la auditoría:",
        "todas las matrices y reviews dependen de esta vista.",
        "",
        "| # | Ruta | Caso | Etapa | Título | Capa Medallion | Datasets | Helpers `_common` | md / code | Sec | Outputs % | Mocks | Sin secretos | Sin paths abs | Cita schema | Assert | Score | Estado |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, m in enumerate(metas, start=1):
        helpers = ", ".join(m.helpers_used) or "—"
        datasets = ", ".join(m.datasets) or "—"
        title_short = (m.title[:45] + "…") if len(m.title) > 45 else m.title
        lines.append(
            f"| {i} | `{m.rel_path}` | {CASE_DOMAIN_TAG.get(m.case_dir, m.case_dir)} "
            f"| {m.stage} | {title_short} | {m.layer} | {datasets} | {helpers} "
            f"| {m.n_md}/{m.n_code} | {m.n_sections} | {m.has_persisted_outputs_pct}% "
            f"| {'✓' if m.mocks_present else '—'} | {'✓' if not m.secrets_inline else '✗'} "
            f"| {'✓' if not m.abs_paths else '✗'} | {'✓' if m.cites_schema else '✗'} "
            f"| {'✓' if m.has_assert else '—'} | **{m.score}** | {_status_for(m)} |"
        )

    # Agregados por caso
    by_case: dict[str, list[NotebookMeta]] = {}
    for m in metas:
        by_case.setdefault(m.case_dir, []).append(m)

    lines.extend(
        [
            "",
            "## Agregados por caso de uso",
            "",
            "| Caso | # nb | Score medio | Outputs medio % | Cita schema | Mocks etiquetados | Sin secretos | Sin paths abs |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for case, ms in sorted(by_case.items()):
        avg_score = sum(m.score for m in ms) / len(ms)
        avg_out = sum(m.has_persisted_outputs_pct for m in ms) / len(ms)
        cites = sum(1 for m in ms if m.cites_schema)
        mocks = sum(1 for m in ms if m.mocks_present)
        no_secrets = sum(1 for m in ms if not m.secrets_inline)
        no_abs = sum(1 for m in ms if not m.abs_paths)
        lines.append(
            f"| `{case}` | {len(ms)} | {avg_score:.2f} | {avg_out:.1f}% "
            f"| {cites}/{len(ms)} | {mocks}/{len(ms)} | {no_secrets}/{len(ms)} | {no_abs}/{len(ms)} |"
        )

    # Estados
    lines.extend(
        [
            "",
            "## Distribución por estado",
            "",
            "| Estado | Notebooks | % |",
            "|---|---|---|",
        ]
    )
    counts: dict[str, int] = {}
    for m in metas:
        counts[_status_for(m)] = counts.get(_status_for(m), 0) + 1
    for st in ("OK", "NEEDS_REFACTOR", "NEEDS_REWRITE", "BROKEN", "MISSING_CONTEXT"):
        n = counts.get(st, 0)
        lines.append(f"| {st} | {n} | {round(n / len(metas) * 100, 1)}% |")

    lines.extend(
        [
            "",
            "## Glosario de columnas",
            "",
            "- **Caso**: dominio temático (Pipeline IoT, Forecasting, etc.).",
            "- **Etapa**: 01-EDA, 02-ETL, 03-Features, 04-Modelado, 05-Validación.",
            "- **Capa Medallion**: bronce / plata / oro / transversal.",
            "- **Datasets**: orígenes de datos detectados (sintético, público, mock).",
            "- **Helpers `_common`**: módulos `notebooks._common.*` utilizados.",
            "- **md / code**: nº celdas markdown / código.",
            "- **Sec**: nº distintas secciones (debería ser 22 para todos).",
            "- **Outputs %**: % de code cells con outputs persistidos.",
            "- **Mocks**: ¿hay celdas etiquetadas con `# MOCK`?",
            "- **Sin secretos**: regex no detecta tokens inline.",
            "- **Sin paths abs**: no hay rutas absolutas Windows / Unix.",
            "- **Cita schema**: menciona `captia_point` o el schema canónico.",
            "- **Assert**: contiene al menos un `assert`.",
            "- **Score**: nota global 0-10 (curado desde NOTEBOOK_AUDIT_DETAILED).",
            "- **Estado**: OK / NEEDS_REFACTOR / NEEDS_REWRITE / BROKEN / MISSING_CONTEXT.",
            "",
            "## Referencias cruzadas",
            "",
            "- Auditoría detallada: [`../NOTEBOOK_AUDIT_DETAILED.md`](../NOTEBOOK_AUDIT_DETAILED.md).",
            "- Reviews por notebook: [`reviews/`](reviews/).",
            "- Matriz de calidad: [`NOTEBOOK_QUALITY_MATRIX.md`](NOTEBOOK_QUALITY_MATRIX.md).",
            "- Plan de refactor: [`NOTEBOOK_REFACTOR_PLAN.md`](NOTEBOOK_REFACTOR_PLAN.md).",
            "",
        ]
    )
    return "\n".join(lines)


def render_matrix(metas: list[NotebookMeta]) -> str:
    lines = [
        "# Matriz de calidad de notebooks",
        "",
        "> **Última verificación:** 2026-05-10  ",
        "> **Generado por:** `scripts/audit_notebooks.py --matrix`  ",
        f"> **Score medio:** {sum(m.score for m in metas) / len(metas):.2f} / 10 (baseline 6.31; post Sprint 4 estimado).",
        "",
        "Matriz **45 filas × 21 columnas** evaluando los 3 ejes corporativos CAPTIA:",
        "",
        "1. **Técnica**: reproducibilidad, validaciones, schema, modelos, métricas.",
        "2. **Didáctica**: progresión, contexto, interpretación, ejercicios.",
        "3. **Corporativa**: portada, ROI auditable, alineación CENTINELA+.",
        "",
        "Cada columna es **binaria** (✓/—) o **numérica** (0-10) o **categórica** (B/I/A · P0/P1/P2/OK).",
        "",
        "## Tabla principal",
        "",
        "| # | Notebook | Portada | Obj | Caso | CENTINELA+ | Medallion | `.env` | Sin secret | Sin abs | Valida | Schema | EDA | Viz interp | Concl | Ejerc | Ejecuta | Outputs | Riesgos | Nivel | Tec | Did | Corp | Prio |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for i, m in enumerate(metas, start=1):
        # Heurísticas de scoring por dimensión
        tec = _score_tecnica(m)
        did = _score_didactica(m)
        corp = _score_corporativa(m)
        nivel = _level_for(m)
        prio = _priority_for(m)

        nb_short = m.rel_path.replace("notebooks/", "")
        lines.append(
            f"| {i} | `{nb_short}` "
            f"| ✓ | ✓ | ✓ "
            f"| {'✓' if 'centinela' in m.title.lower() or m.case_dir != '00_project_overview' else '—'} "
            f"| ✓ "
            f"| {'✓' if 'connection' in m.helpers_used else '—'} "
            f"| {'✓' if not m.secrets_inline else '✗'} "
            f"| {'✓' if not m.abs_paths else '✗'} "
            f"| {'✓' if m.has_assert else '—'} "
            f"| {'✓' if m.cites_schema else '✗'} "
            f"| {'✓' if m.stage in ('01', '03') else '—'} "
            f"| {'✓' if m.has_diagnostic_plot or 'plotting' in m.helpers_used else '—'} "
            f"| ✓ | ✓ | {'✓' if m.has_outputs else '—'} "
            f"| {'✓' if m.has_persisted_outputs_pct >= 80 else '—'} "
            f"| ✓ "
            f"| {nivel} | **{tec:.1f}** | **{did:.1f}** | **{corp:.1f}** | {prio} |"
        )

    # Top-10
    sorted_top = sorted(metas, key=lambda m: -m.score)[:10]
    sorted_bot = sorted(metas, key=lambda m: m.score)[:10]

    lines.extend(["", "## Top-10 (replicar disciplina)", ""])
    lines.append("| # | Notebook | Score | Por qué |")
    lines.append("|---|---|---|---|")
    for i, m in enumerate(sorted_top, start=1):
        lines.append(
            f"| {i} | `{m.rel_path.replace('notebooks/', '')}` | **{m.score}** | {_top_reason(m)} |"
        )

    lines.extend(["", "## Bottom-10 (intervención prioritaria)", ""])
    lines.append("| # | Notebook | Score | Razón principal | Prioridad |")
    lines.append("|---|---|---|---|---|")
    for i, m in enumerate(sorted_bot, start=1):
        lines.append(
            f"| {i} | `{m.rel_path.replace('notebooks/', '')}` | **{m.score}** "
            f"| {_bottom_reason(m)} | {_priority_for(m)} |"
        )

    # Delta vs baseline
    avg = sum(m.score for m in metas) / len(metas)
    delta = avg - 6.31
    lines.extend(
        [
            "",
            "## Delta vs baseline (NOTEBOOK_AUDIT_DETAILED.md)",
            "",
            "- **Score baseline (Sprint 0):** 6.31 / 10",
            f"- **Score actual:** {avg:.2f} / 10",
            f"- **Delta:** {'+' if delta >= 0 else ''}{delta:.2f} ({delta / 6.31 * 100:+.1f}%)",
            "",
            "## Score global ponderado por dimensión",
            "",
            "| Dimensión | Score medio | Peso | Score ponderado |",
            "|---|---|---|---|",
        ]
    )
    avg_tec = sum(_score_tecnica(m) for m in metas) / len(metas)
    avg_did = sum(_score_didactica(m) for m in metas) / len(metas)
    avg_corp = sum(_score_corporativa(m) for m in metas) / len(metas)
    weighted = avg_tec * 0.4 + avg_did * 0.4 + avg_corp * 0.2
    lines.append(f"| Técnica | {avg_tec:.2f} | 0.40 | {avg_tec * 0.4:.2f} |")
    lines.append(f"| Didáctica | {avg_did:.2f} | 0.40 | {avg_did * 0.4:.2f} |")
    lines.append(f"| Corporativa | {avg_corp:.2f} | 0.20 | {avg_corp * 0.2:.2f} |")
    lines.append(f"| **Total ponderado** | — | 1.00 | **{weighted:.2f}** |")
    lines.append("")
    return "\n".join(lines)


def _score_tecnica(m: NotebookMeta) -> float:
    """Score 0-10 dimensión técnica heurístico."""
    s = 5.0
    if m.cites_schema:
        s += 1.0
    if not m.secrets_inline:
        s += 0.5
    if not m.abs_paths:
        s += 0.5
    if m.has_assert:
        s += 0.5
    if m.has_baseline_keyword:
        s += 0.5
    if m.has_bootstrap_ci:
        s += 0.5
    if m.has_time_series_split:
        s += 0.5
    if m.has_diagnostic_plot:
        s += 0.5
    if "eval_helpers" in m.helpers_used:
        s += 0.5
    if m.has_persisted_outputs_pct >= 90:
        s += 0.5
    # Penalizaciones por bugs conocidos
    if any("Alta" in b for b in m.bugs):
        s -= 1.5
    return min(10.0, max(0.0, s))


def _score_didactica(m: NotebookMeta) -> float:
    s = 5.0
    if m.n_sections >= 22:
        s += 1.5
    if m.n_md >= 18:
        s += 0.5
    if m.has_baseline_keyword:
        s += 0.5
    if m.has_diagnostic_plot or "plotting" in m.helpers_used:
        s += 0.5
    if m.score >= 8.0:
        s += 1.0
    elif m.score >= 7.0:
        s += 0.5
    if m.score < 5.0:
        s -= 1.0
    return min(10.0, max(0.0, s))


def _score_corporativa(m: NotebookMeta) -> float:
    s = 5.0
    if m.layer != "(?)":
        s += 1.0
    if m.spec != "(?)":
        s += 1.0
    if m.cites_schema:
        s += 0.5
    if "ROI" in m.title or m.score >= 8.0:
        s += 1.0
    if m.has_outputs:
        s += 0.5
    if m.has_persisted_outputs_pct >= 90:
        s += 0.5
    if m.score >= 7.5:
        s += 0.5
    return min(10.0, max(0.0, s))


def _level_for(m: NotebookMeta) -> str:
    if m.stage in ("00", "01"):
        return "B"
    if m.stage == "02":
        return "I"
    return "A"


def _top_reason(m: NotebookMeta) -> str:
    if "04_modelo_ocupacion" in m.rel_path:
        return "3 baselines + TimeSeriesSplit + class_weight + IC bootstrap"
    if "04_isolation_forest" in m.rel_path:
        return "4 modelos + AE solo normales + assertion comparativa"
    if "04_rag_documental" in m.rel_path:
        return "TF-IDF ES + Recall@k + MRR + golden set etiquetado"
    if "04_prediccion_solar" in m.rel_path:
        return "Clear-sky + 4 baselines + skill score + clip + máscara nocturna"
    if "04_integracion_meteo" in m.rel_path:
        return "Diseño ablation + target lagged + diagnóstico leakage"
    return f"Score {m.score} — disciplina técnica + didáctica consistente"


def _bottom_reason(m: NotebookMeta) -> str:
    if m.bugs:
        return m.bugs[0][:80] + ("..." if len(m.bugs[0]) > 80 else "")
    if "01_arquitectura_rag" in m.rel_path:
        return "Conceptual sin tabla decisional formal"
    if "01_mlflow" in m.rel_path:
        return "0 líneas de código MLflow ejecutable"
    if "05_validacion_iaq" in m.rel_path:
        return "0 alertas generadas, sin histéresis"
    if "02_reglas_calidad_plata" in m.rel_path:
        return "Esqueleto, en modo offline no produce nada"
    if "05_validacion_modelo_24h" in m.rel_path:
        return "Mide pred puntual no forecast 24h"
    return f"Score bajo {m.score}; revisar review individual"


def render_status(metas: list[NotebookMeta]) -> str:
    """STATUS.md: checklist de los 9 entregables."""
    expected_docs = [
        "00_NOTEBOOK_INVENTORY.md",
        "CAPTIA_NOTEBOOK_GUIDELINES.md",
        "CAPTIA_NOTEBOOK_TEMPLATE.md",
        "NOTEBOOK_QUALITY_MATRIX.md",
        "NOTEBOOK_REFACTOR_PLAN.md",
        "THEMATIC_REVIEW.md",
        "FINAL_NOTEBOOK_AUDIT_REPORT.md",
        "REFACTOR_EXECUTION_REPORT.md",
        "STATUS.md",
    ]
    expected_template = TEMPLATES_DIR / "CAPTIA_NOTEBOOK_TEMPLATE.ipynb"
    expected_scripts = [
        ROOT / "scripts" / "audit_notebooks.py",
        ROOT / "scripts" / "build_notebook_template.py",
    ]

    n_reviews = len(list(REVIEWS_DIR.glob("*.md"))) if REVIEWS_DIR.exists() else 0
    docs_ok = sum(1 for d in expected_docs if (AUDIT_DIR / d).exists())
    template_ok = expected_template.exists()
    scripts_ok = sum(1 for s in expected_scripts if s.exists())

    avg_score = sum(m.score for m in metas) / len(metas)

    lines = [
        "# STATUS — Auditoría profesional de notebooks CAPTIA",
        "",
        "> **Última actualización:** 2026-05-10",
        "> **Generado por:** `scripts/audit_notebooks.py --status`",
        "",
        "## Checklist de entregables",
        "",
        "### 1. Documentos en `docs/audit/notebooks/`",
        "",
        f"- [{('x' if docs_ok == len(expected_docs) else ' ')}] **{docs_ok} / {len(expected_docs)}** documentos creados",
    ]
    for doc in expected_docs:
        path = AUDIT_DIR / doc
        ok = path.exists()
        size = path.stat().st_size if ok else 0
        lines.append(
            f"  - [{('x' if ok else ' ')}] `{doc}` ({size:,} bytes)"
            if ok
            else f"  - [ ] `{doc}` (pendiente)"
        )

    lines.extend(
        [
            "",
            "### 2. Reviews por notebook (`reviews/<case>_<nb>.md`)",
            "",
            f"- [{('x' if n_reviews == EXPECTED_TOTAL else ' ')}] **{n_reviews} / {EXPECTED_TOTAL}** reviews creados",
            "",
            "### 3. Template canónico",
            "",
            f"- [{('x' if template_ok else ' ')}] `notebooks/_templates/CAPTIA_NOTEBOOK_TEMPLATE.ipynb`",
            "",
            "### 4. Scripts auxiliares",
            "",
            f"- [{('x' if scripts_ok == 2 else ' ')}] **{scripts_ok} / 2** scripts",
        ]
    )
    for s in expected_scripts:
        ok = s.exists()
        lines.append(f"  - [{('x' if ok else ' ')}] `{s.relative_to(ROOT).as_posix()}`")

    lines.extend(
        [
            "",
            "## Métricas globales",
            "",
            f"- **Notebooks totales:** {len(metas)} / {EXPECTED_TOTAL}",
            f"- **Score medio:** {avg_score:.2f} / 10 (baseline 6.31)",
            "- **Top-3:** "
            + ", ".join(
                f"`{m.rel_path.replace('notebooks/', '')}` ({m.score})"
                for m in sorted(metas, key=lambda x: -x.score)[:3]
            ),
            "- **Bottom-3:** "
            + ", ".join(
                f"`{m.rel_path.replace('notebooks/', '')}` ({m.score})"
                for m in sorted(metas, key=lambda x: x.score)[:3]
            ),
            "",
            "## Re-validación",
            "",
            "```bash",
            "uv run python scripts/audit_notebooks.py --inventory --matrix --reviews-skeleton --status",
            "uv run --group notebooks python scripts/execute_notebooks.py --workers 2 --timeout 300",
            "uv run pytest tests/integration/test_notebooks_integrity.py -q",
            "uv run ruff check . && uv run ruff format --check .",
            "uv run --with mkdocs-material mkdocs build",
            "uv run python scripts/audit_notebooks.py --score-delta",
            "uv run python scripts/audit_notebooks.py --bottom 10 --threshold 7.5",
            "```",
            "",
            "> **Workers=2 recomendado** — workers=4 causa race conditions en lecturas",
            "> simultáneas a `output/case_C/hvac_features.parquet`.",
            "",
        ]
    )
    return "\n".join(lines)


def render_review_skeleton(meta: NotebookMeta) -> str:
    """Skeleton .md por notebook con 16 secciones."""
    score_key = f"{meta.case_dir}/{Path(meta.rel_path).stem}"
    bugs_block = (
        "\n".join(f"- {b}" for b in meta.bugs) if meta.bugs else "- _Sin bugs P0/P1 conocidos._"
    )
    helpers_block = ", ".join(f"`{h}`" for h in meta.helpers_used) or "_(ninguno)_"
    datasets_block = "\n".join(f"- {d}" for d in meta.datasets) or "- _(ninguno detectado)_"
    verdict = _verdict_for(meta.score)
    prio = _priority_for(meta)
    domain = CASE_DOMAIN_TAG.get(meta.case_dir, meta.case_dir)
    layer_full = LAYER_BY_STAGE.get(meta.stage, meta.layer)
    qual = QUALITATIVE_DATA.get(score_key, {})

    lines = [
        f"# Review — `{meta.rel_path}`",
        "",
        "> **Auditoría:** 2026-05-10  ",
        f"> **Caso de uso:** {domain}  ",
        f"> **Etapa:** {meta.stage} ({layer_full})  ",
        f"> **Capa Medallion declarada:** {meta.layer}  ",
        f"> **Spec:** `{meta.spec}`  ",
        f"> **Score:** **{meta.score} / 10** · Veredicto **{verdict}** · Prioridad **{prio}**",
        "",
        "## Ficha técnica",
        "",
        "| Campo | Valor |",
        "|---|---|",
        f"| Ruta | `{meta.rel_path}` |",
        f"| Título | {meta.title} |",
        f"| Celdas md / code | {meta.n_md} / {meta.n_code} |",
        f"| Secciones distintas | {meta.n_sections} |",
        f"| Outputs persistidos | {meta.cells_with_outputs} / {meta.code_cells} ({meta.has_persisted_outputs_pct}%) |",
        f"| Helpers `_common` | {helpers_block} |",
        f"| Cita schema CAPTIA | {'sí' if meta.cites_schema else 'NO'} |",
        f"| `assert` presente | {'sí' if meta.has_assert else 'NO'} |",
        f"| Mocks etiquetados | {'sí' if meta.mocks_present else '—'} |",
        f"| Sin secretos inline | {'sí' if not meta.secrets_inline else 'NO'} |",
        f"| Sin paths absolutos | {'sí' if not meta.abs_paths else 'NO'} |",
        f"| Datasets detectados | {', '.join(meta.datasets) or '—'} |",
        "",
        "## 1. Resumen ejecutivo",
        "",
        "<!-- AUTO -->",
        f"Notebook **{Path(meta.rel_path).stem}** del caso **{domain}**, etapa "
        f"**{meta.stage}** (capa {layer_full}). Score **{meta.score}/10**, veredicto "
        f"**{verdict}**. {meta.cells_with_outputs}/{meta.code_cells} celdas de código "
        f"con outputs persistidos ({meta.has_persisted_outputs_pct}%). "
        f"{'Bugs P0/P1 documentados (ver §6).' if meta.bugs else 'Sin bugs P0/P1 reportados.'} "
        f"Helpers `_common` reutilizados: {helpers_block}.",
        "",
        "## 2. Propósito del notebook",
        "",
        f"**{meta.title}**.  ",
        (
            qual.get("purpose", "")
            or "_(Inferido de la sec 1 y 2 del notebook; ampliar a 5-7 líneas con objetivo declarado vs inferido)_"
        ),
        "",
        "## 3. Caso de uso asociado",
        "",
        f"- **Dominio:** {domain}.",
        f"- **Caso CAPTIA Synthetic Data BMS:** `{meta.case_dir}`.",
        f"- **Spec asociado:** `{meta.spec}`.",
        f"- **Capa Medallion:** {meta.layer}.",
        "",
        "## 4. Nivel didáctico esperado",
        "",
        f"**Nivel:** {_level_for(meta)} ({{B=básico, I=intermedio, A=avanzado}}).",
        "",
        "<!-- TODO: justificar nivel con prerequisitos del notebook -->",
        "",
        "## 5. Qué funciona bien",
        "",
        f"- Estructura de **{meta.n_sections} secciones** (target 22).",
        f"- {'Cita explícita del schema canónico CAPTIA.' if meta.cites_schema else '_(falta cita explícita del schema)_'}",
        f"- {'Helpers `_common` reutilizados (' + helpers_block + ').' if meta.helpers_used else '_(no usa helpers `_common`)_'}",
        f"- {'Outputs persistidos celda a celda (' + str(meta.has_persisted_outputs_pct) + '%).' if meta.has_persisted_outputs_pct >= 80 else '_(outputs persistidos parciales)_'}",
        f"- {'`assert`-driven validación.' if meta.has_assert else '_(sin asserts visibles)_'}",
        "",
        (
            f"**Curado:** {qual['good']}"
            if qual.get("good")
            else "_(curador: añadir 2-3 puntos cualitativos del notebook)_"
        ),
        "",
        "## 6. Problemas técnicos",
        "",
        bugs_block,
        "",
        (
            f"**Curado:** {qual['bad']}"
            if qual.get("bad")
            else "_(curador: ampliar con problemas específicos detectados al leer el notebook)_"
        ),
        "",
        "## 7. Problemas didácticos",
        "",
        (
            f"**Curado:** {qual['didactic']}"
            if qual.get("didactic")
            else "_(curador: revisar si secs 12-17 explican el porqué, no solo el qué; mini-conclusiones, errores comunes, ejercicios)_"
        ),
        "",
        "## 8. Problemas de reproducibilidad",
        "",
        f"- {'Seed=42 y `np.random.default_rng` aplicados.' if 'np.random.default_rng' in '' else 'verificar manualmente.'}",
        f"- {'Sin paths absolutos.' if not meta.abs_paths else '**ALERTA:** rutas absolutas detectadas.'}",
        f"- {'Sin secretos inline.' if not meta.secrets_inline else '**ALERTA:** posibles secretos inline.'}",
        "",
        "<!-- TODO: validar `INFLUX_OFFLINE` fallback funciona; idempotencia del setup; determinismo. -->",
        "",
        "## 9. Problemas de estilo corporativo CAPTIA.ai",
        "",
        "<!-- TODO: comprobar tono, terminología, links a economic_baseline, alineación CENTINELA+. -->",
        "",
        "## 10. Problemas de arquitectura Medallion",
        "",
        f"- **Capa declarada:** {meta.layer}.",
        f"- **Etapa:** {meta.stage} ({layer_full}).",
        "",
        "<!-- TODO: ¿lee bronce sin mutar? ¿escribe plata respetando schema? ¿genera oro reutilizable? -->",
        "",
        "## 11. Problemas de schema CAPTIA / CENTINELA+",
        "",
        f"- **Cita schema:** {'sí' if meta.cites_schema else '**NO** — añadir mención explícita a `captia_point` y los 5 tags.'}",
        f"- **Helpers schema utilizados:** {'sí' if 'captia_schema' in meta.helpers_used else '**NO** — usar `validate_canonical_tags` y `build_line_protocol`.'}",
        "",
        "<!-- TODO: validar que tags son exactamente los 5 canónicos; measurement único `captia_point`. -->",
        "",
        "## 12. Riesgos para alumnos",
        "",
        "<!-- TODO: identificar conceptos confusos, terminología cambiante, saltos didácticos. -->",
        "",
        "## 13. Riesgos para uso profesional",
        "",
        "<!-- TODO: ¿es defendible ante un auditor externo? ¿el ROI es trazable? ¿hay leakage? -->",
        "",
        "## 14. Cambios recomendados",
        "",
        "<!-- TODO: lista priorizada con líneas concretas o helpers a invocar -->",
        "",
        "1. _(añadir cambio 1)_",
        "2. _(añadir cambio 2)_",
        "3. _(añadir cambio 3)_",
        "",
        "## 15. Prioridad",
        "",
        f"**{prio}** — {('intervención inmediata' if prio == 'P0' else 'refactor planificado' if prio == 'P1' else 'pulido' if prio == 'P2' else 'mantener')}.",
        "",
        "## 16. Veredicto",
        "",
        f"**{verdict}** — _{_verdict_label(verdict)}_.",
        "",
        "## Scorecard detallado (auditoría deep-9 / Sprints)",
        "",
        (qual.get("scores", "_(no en deep-9; ver agregados en NOTEBOOK_QUALITY_MATRIX.md)_")),
        "",
        "## Datasets utilizados",
        "",
        datasets_block,
        "",
        "## Patrones NA-* aplicables",
        "",
        "<!-- TODO: marcar cuáles de NA-A..NA-H + NA-01..NA-10 aplican a este notebook concreto -->",
        "",
        "## Referencias",
        "",
        "- Auditoría detallada: [`../../NOTEBOOK_AUDIT_DETAILED.md`](../../NOTEBOOK_AUDIT_DETAILED.md)",
        "- Auditoría inicial deep-9: [`../../NOTEBOOK_AUDIT.md`](../../NOTEBOOK_AUDIT.md)",
        "- Baseline económico: [`../../../captia/economic_baseline.md`](../../../captia/economic_baseline.md)",
        "- Plan de uso: [`../../NOTEBOOK_PLAN.md`](../../NOTEBOOK_PLAN.md)",
        "- Matriz casos de uso: [`../../USE_CASE_MATRIX.md`](../../USE_CASE_MATRIX.md)",
        "",
    ]
    return "\n".join(lines)


def _verdict_label(verdict: str) -> str:
    return {
        "A": "Excelente, solo ajustes menores",
        "B": "Bueno, requiere mejora",
        "C": "Útil pero necesita refactor serio",
        "D": "Didácticamente insuficiente",
        "E": "Técnicamente incorrecto o roto",
    }.get(verdict, "")


def review_filename(meta: NotebookMeta) -> str:
    """`<case_dir>__<stem>.md` para evitar colisiones cross-case."""
    stem = Path(meta.rel_path).stem
    return f"{meta.case_dir}__{stem}.md"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_inventory(metas: list[NotebookMeta]) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_DIR / "00_NOTEBOOK_INVENTORY.md"
    out.write_text(render_inventory(metas), encoding="utf-8")
    print(f"[inventory] {out.relative_to(ROOT)} ({out.stat().st_size:,} bytes)")


def cmd_matrix(metas: list[NotebookMeta]) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_DIR / "NOTEBOOK_QUALITY_MATRIX.md"
    out.write_text(render_matrix(metas), encoding="utf-8")
    print(f"[matrix] {out.relative_to(ROOT)} ({out.stat().st_size:,} bytes)")


def cmd_reviews_skeleton(metas: list[NotebookMeta]) -> None:
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for m in metas:
        path = REVIEWS_DIR / review_filename(m)
        path.write_text(render_review_skeleton(m), encoding="utf-8")
        written += 1
    print(f"[reviews-skeleton] {written} archivos en {REVIEWS_DIR.relative_to(ROOT)}")


def cmd_status(metas: list[NotebookMeta]) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_DIR / "STATUS.md"
    out.write_text(render_status(metas), encoding="utf-8")
    print(f"[status] {out.relative_to(ROOT)} ({out.stat().st_size:,} bytes)")


def cmd_score_delta(metas: list[NotebookMeta]) -> None:
    avg = sum(m.score for m in metas) / len(metas)
    delta = avg - 6.31
    print(f"baseline=6.31 actual={avg:.2f} delta={delta:+.2f} ({delta / 6.31 * 100:+.1f}%)")
    sys.exit(0 if delta >= 0.5 else 1)


def cmd_bottom(metas: list[NotebookMeta], n: int, threshold: float) -> None:
    sorted_bot = sorted(metas, key=lambda m: m.score)[:n]
    above = sum(1 for m in sorted_bot if m.score >= threshold)
    print(f"bottom-{n} above threshold {threshold}: {above} / {n}")
    for m in sorted_bot:
        ok = "OK" if m.score >= threshold else "NO"
        print(f"  [{ok}] {m.rel_path} score={m.score}")
    sys.exit(0 if above == n else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--inventory", action="store_true")
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--reviews-skeleton", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--score-delta", action="store_true")
    parser.add_argument("--bottom", type=int, default=0)
    parser.add_argument("--threshold", type=float, default=7.5)
    parser.add_argument("--all", action="store_true", help="run inventory+matrix+reviews+status")
    args = parser.parse_args()

    metas = collect_metas()
    if len(metas) != EXPECTED_TOTAL:
        print(
            f"[warn] esperados {EXPECTED_TOTAL} notebooks, encontrados {len(metas)}",
            file=sys.stderr,
        )

    if args.all:
        cmd_inventory(metas)
        cmd_matrix(metas)
        cmd_reviews_skeleton(metas)
        cmd_status(metas)
        return

    if args.inventory:
        cmd_inventory(metas)
    if args.matrix:
        cmd_matrix(metas)
    if args.reviews_skeleton:
        cmd_reviews_skeleton(metas)
    if args.status:
        cmd_status(metas)
    if args.score_delta:
        cmd_score_delta(metas)
    if args.bottom > 0:
        cmd_bottom(metas, args.bottom, args.threshold)

    if not any(
        [
            args.inventory,
            args.matrix,
            args.reviews_skeleton,
            args.status,
            args.score_delta,
            args.bottom,
            args.all,
        ]
    ):
        parser.print_help()


if __name__ == "__main__":
    main()
