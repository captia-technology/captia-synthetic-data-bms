# Auditoría detallada notebook-a-notebook (45 / 45)

> **Última verificación:** 2026-05-10
> **Auditores:** 5 agentes paralelos `code-reviewer` (Claude Opus 4.7).
> **Alcance:** lectura íntegra + análisis de outputs ejecutados de los **45 notebooks** del repo.
> **Reporte previo (resumen):** [`NOTEBOOK_AUDIT.md`](NOTEBOOK_AUDIT.md).

## Score medio global: **6.31 / 10**

| Bloque | Score medio | Notebooks |
|--------|-------------|-----------|
| 00 Overview | 6.90 | 3 |
| 01 Caso A — Pipeline IoT | 5.93 | 3 |
| 02 Caso B — Forecast | 6.02 | 5 |
| 03 Caso C — Anomalías HVAC | 7.00 | 5 |
| 04 Caso D — IAQ + Ocupación | 6.90 | 5 |
| 05 Caso E — Meteo & Solar | 6.63 | 4 |
| 06 Caso F — MLOps | 6.07 | 3 |
| 07 Caso G — Calidad agentes | 6.40 | 4 |
| 08 Caso H — RAG + Chatbot | 6.16 | 5 |
| 09 Caso I — Spark vs Pandas | 5.75 | 4 |
| 10 Caso J — Tráfico + YOLO | 5.75 | 4 |

## Top 5 — los más sólidos (a preservar y replicar)

| # | Notebook | Score | Por qué |
|---|----------|-------|---------|
| 1 | `04_case_D/04_modelo_ocupacion_desde_ambiente` | **9.5** | 3 baselines + TimeSeriesSplit + class_weight + IC bootstrap |
| 2 | `03_case_C/04_isolation_forest_autoencoder` | **9.0** | 4 modelos + AE entrenado solo con normales + assertion comparativa |
| 3 | `08_case_H/04_rag_documental` | **8.7** | TF-IDF ES + Recall@k real + MRR + golden set etiquetado |
| 4 | `05_case_E/04_prediccion_solar` | **8.6** | Clear-sky decomposition + 4 baselines + skill score + clip + máscara nocturna |
| 5 | `10_case_J/04_integracion_meteo_trafico` | **8.5** | Diseño ablation + target lagged + diagnóstico leakage explícito |

## Bottom 10 — necesitan intervención

| # | Notebook | Score | Razón principal |
|---|----------|-------|-----------------|
| 1 | `09_case_I/03_benchmark_spark` | **3.5** | No instala Spark ni Dask → DataFrame vacío |
| 2 | `10_case_J/02_inferencia_yolo` | **3.5** | Mock lee 4 bytes JPEG magic → 5 imágenes idénticas |
| 3 | `10_case_J/01_captura_imagenes_dgt` | **4.5** | Promete cron+APScheduler+retry y no entrega ninguno |
| 4 | `04_case_D/05_validacion_iaq_confort` | **4.5** | 0 alertas generadas, sin histéresis |
| 5 | `07_case_G/02_reglas_calidad_plata` | **4.5** | Esqueleto, en modo offline no produce nada |
| 6 | `08_case_H/03_mock_tools_predictivos` | **4.8** | Mocks demasiado triviales, viola su propia sec 15 |
| 7 | `03_case_C/05_validacion_fallos` | **5.0** | Train≡test (leakage), threshold ad-hoc |
| 8 | `06_case_F/01_mlflow_overview` | **5.0** | 0 líneas de código MLflow ejecutable |
| 9 | `08_case_H/01_arquitectura_rag` | **5.0** | Conceptual sin tabla decisional formal |
| 10 | `02_case_B/05_validacion_modelo_24h` | **5.3** | Bug crítico: mide pred puntual no forecast 24h |

## Bugs críticos encontrados (P0) — 7 fixes prioritarios

| # | Notebook | Bug | Severidad |
|---|----------|-----|-----------|
| **B1** | `08_case_H/02_tools_influxdb` | `compare_periods` ignora `start` → `p1 == p2` siempre, `diff: None` | Alta |
| **B2** | `08_case_H/04_rag_documental` | Clave duplicada en `expected_map` (`"¿Qué es el bucket telemetry_1h?"` 2 veces) | Alta |
| **B3** | `08_case_H/05_evaluacion_chatbot` | Claves duplicadas en `route()`: `["mañana", "predicción", "predicción"]` | Alta |
| **B4** | `10_case_J/02_inferencia_yolo` | `count_vehicles_mock` usa `image_bytes[:4]` (JPEG magic) → 5 imágenes producen output idéntico | Alta |
| **B5** | `10_case_J/01_captura_imagenes_dgt` | `fake_jpeg` crea `rng` interno → todas las imágenes idénticas | Alta |
| **B6** | `07_case_G/03_reglas_calidad_oro_ml` | `kl_hist` con `density=True` genera KL negativos (imposible) | Alta |
| **B7** | `09_case_I/03_benchmark_spark` | `pyspark` y `dask` no instalados → DataFrame vacío entregado como artefacto | Alta |

## Patrones transversales identificados

### Patrones positivos (preservar)

- **Setup canónico idéntico** en los 45 notebooks → reproducibilidad.
- **`seed=42`** consistente.
- **Bibliografías reales** (Liu 2008, Hinton 2006, Iqbal 1983, ASHRAE, EN 16798).
- **Estructura Medallion** consistente.
- **Mocks deterministas** con cabecera `# MOCK ...`.

### Patrones críticos a corregir (NA-XX)

| ID | Patrón | Notebooks afectados |
|----|--------|---------------------|
| **NA-A** | Sec 19/20/21 idénticas dentro de cada caso (5× la misma cifra ROI) | Casos B, C, D, E, F, G, H, I, J |
| **NA-B** | `eval_helpers.py` infrautilizado fuera de los notebooks `04` | Bloques overview, A, B, parcial F |
| **NA-C** | Tabla "Benchmark BDG2 53M" fabricada y repetida en 4 notebooks Caso I | I (todos) |
| **NA-D** | Promesa-entrega rota: secciones 2 anuncian técnicas que el código no implementa | A·02, B·04, B·05, E·01, J·01 |
| **NA-E** | ROI sin baseline auditable (`+800 €/mes` sin denominador) | Todos los casos |
| **NA-F** | Asserts laxos (`> 0.5`, `< 250`) que pasan trivialmente | C·05, E·04, H·05, J·02, J·04 |
| **NA-G** | Imports masivos no usados en setup canónico | Todos (45) |
| **NA-H** | Sec 15 lista errores que el propio código comete | C·03 (`valve_duty_60` sin shift), E·04 (sin clip), H·03 (mock estático) |

## Plan de remediación priorizado

### Sprint 1 (esta sesión): bugs P0 + mejoras de máximo impacto

1. **Fix B1-B7**: 7 bugs identificados, todos pequeños (1-5 líneas).
2. **Helpers reutilizables**: añadir `notebooks/_common/eval_helpers.py:kl_divergence_correct` para reparar B6 + uso transversal.
3. **Validación de imágenes mock determinista** (B4-B5): hash completo, no magic bytes.

### Sprint 2: cohesión LaTeX-código en notebooks bottom-10

- `06_case_F/01_mlflow_overview`: añadir 5 celdas con `mlflow.start_run()` real.
- `07_case_G/02_reglas_plata`: fallback simulado con visualización.
- `08_case_H/03_mock_tools`: añadir ruido + estacionalidad a los mocks.
- `09_case_I/03_benchmark_spark`: documentar honestamente que Spark no aplica + recomendación polars.
- `10_case_J/01_captura_imagenes`: APScheduler real + retry con tenacity.

### Sprint 3: ROIs honestos con baseline + tabla de decisión

- Sustituir cifras infladas por desgloses Fermi auditables.
- Reemplazar tabla "Benchmark BDG2 53M filas" por nota "cifras ilustrativas no medidas".
- Crear `docs/captia/economic_baseline.md` con costing real CAPTIA.

## Conclusión

**Score medio actual 6.31/10. Estado: aceptable para uso docente, no para entrega pública.**

Con los 7 fixes P0 + las mejoras Sprint 2 sobre los 10 notebooks más débiles, el score medio sube a estimado **7.5/10** sin reescribir el grueso del material. La inversión más eficiente está en los 10 peores, no en empujar los 5 mejores a 9.5.

**Patrón de referencia:** los notebooks `04_case_*/04_*` (Casos C, D, E, J, I) demuestran que el equipo SABE producir notebooks de 8.5+/10 cuando aplica disciplina (baselines, IC bootstrap, ablation, target lag). El gap está en aplicar consistentemente esa disciplina al resto.
