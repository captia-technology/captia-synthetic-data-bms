# Revisión temática avanzada — 13 capítulos

> **Última verificación:** 2026-05-10
> **Alcance:** los 45 notebooks del repo, agrupados por temática técnica.
> **Vinculado a:** [`NOTEBOOK_QUALITY_MATRIX.md`](NOTEBOOK_QUALITY_MATRIX.md) (scores) · [`reviews/`](reviews/) (reviews por nb).

Esta revisión cruza los 45 notebooks por **13 ejes temáticos** que
CAPTIA cubre en el Curso de Especialización IA & Big Data 2025-2026.
Para cada temática:

- **Qué debe enseñar** (objetivos pedagógicos).
- **Qué NO debe hacer** (anti-patrones específicos).
- **Errores comunes** que el alumno cometerá.
- **Checklist específico** de cumplimiento.
- **Notebooks relacionados** (con score actual).
- **Gaps detectados** y recomendaciones.

---

## 1. Pipeline IoT — MQTT, Telegraf, InfluxDB

**Score medio temática:** 5.93 / 10 (Caso A · 3 notebooks).

### Qué debe enseñar

- Cómo se mueve un dato desde el sensor hasta Grafana.
- Topics MQTT jerárquicos `captia/{env}/{tenant}/{site}/{device}/telemetry/{name}`.
- Calidad de servicio (QoS 0 / 1 / 2) y cuándo usar cada uno.
- Throughput esperado (CENTINELA+ ≈ 308 msg/s con 70 aulas).
- Telegraf MQTT consumer con regex parsing.
- InfluxDB write API y políticas de retención.

### Qué NO debe hacer

- Mostrar curvas teóricas de queueing sin medir nada.
- Asumir QoS=1 sin justificarlo.
- Hardcodear credenciales MQTT.
- Olvidar healthchecks Mosquitto.
- Mezclar bytes JPEG (Caso J) con telemetría continua.

### Errores comunes

1. **Cliente lento** que no consume al ritmo del broker → buffer overflow.
2. **Topics planos** (`telemetry`) en lugar de jerárquicos.
3. **Reusar mismo `client_id`** entre publicadores → desconexiones.
4. **Bridges sin TLS** en producción.

### Checklist específico

- [ ] Mide throughput **real** vs λ teórico.
- [ ] Documenta QoS y por qué.
- [ ] Usa `paho-mqtt` real (con fallback in-memory).
- [ ] Schema canónico citado y validado.
- [ ] Telegraf regex documentado.

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `01_case_A/01_explicacion_pipeline_centinela` | 6.5 | NEEDS_REFACTOR |
| `01_case_A/02_publicacion_mqtt_a_influxdb` | 6.0 | NEEDS_REFACTOR |
| `01_case_A/03_validacion_telegraf_influx_grafana` | 5.3 | NEEDS_REWRITE |

### Gaps detectados

- A·02 promete benchmark queueing teórico (sec 19) que no se ejecuta (NA-D).
- A·03 mide validación pero falta tabla decisional para troubleshooting (Telegraf restart, InfluxDB 401, Mosquitto unhealthy).
- Falta cobertura de **TLS / autenticación MQTT real**.

---

## 2. InfluxDB / Flux — queries y downsampling

**Score medio temática:** 6.40 / 10 (Casos G · plata + A·03 + H·02).

### Qué debe enseñar

- Sintaxis Flux básica (`from(bucket) |> range() |> filter() |> aggregateWindow()`).
- Downsampling tasks (`telemetry → telemetry_1m → telemetry_15m → telemetry_1h`).
- Buckets y políticas de retención.
- `tags` vs `fields` (cuándo cada uno).
- Joins entre buckets (state_events × telemetry).
- Notification rules para alertas.

### Qué NO debe hacer

- Indexar series temporales como texto en RAG (separar tools de RAG).
- Crear measurements distintos para cada variable (rompería el schema canónico).
- Olvidar `start: -<duration>` en queries (full-scan).

### Errores comunes

1. Tagear el `value` como tag en lugar de field → cardinalidad explota.
2. Usar `aggregateWindow(every: 1s)` sobre 14 días → query timeout.
3. Filtrar por tag con regex sin `\b...\b` → matches inesperados.

### Checklist específico

- [ ] Cita measurement `captia_point` y los 5 tags.
- [ ] Usa `validate_canonical_tags()`.
- [ ] Demuestra al menos 1 Flux task de downsampling.
- [ ] Compara query Flux vs Pandas vs DuckDB.

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `00_overview/01_schema_captia_influxdb` | 7.0 | OK |
| `00_overview/02_conexion_influxdb_y_variables_entorno` | 6.5 | NEEDS_REFACTOR |
| `07_case_G/02_reglas_calidad_plata_influxdb` | 4.5 | NEEDS_REWRITE |
| `08_case_H/02_tools_influxdb` | 6.5 | NEEDS_REFACTOR |

### Gaps detectados

- G·02 en modo offline NO produce nada (esqueleto).
- H·02 tenía B1 (compare_periods bug); resuelto Sprint 1.
- Falta notebook dedicado a **Flux Tasks de downsampling** (o más detalle en G·02).

---

## 3. Arquitectura Medallion (bronce / plata / oro)

**Score medio temática:** transversal a los 45.

### Qué debe enseñar

- Las 3 capas y qué transformación ocurre en cada paso.
- **Contrato CAPTIA:** plata = `captia_point` + 5 tags + `value`.
- Reglas de oro:
  - **Bronce inmutable** (nunca mutar).
  - **Plata canónica** (schema rígido).
  - **Oro reutilizable** (features, modelos).
- Diagrama Mermaid claro.

### Qué NO debe hacer

- Cambiar nombres de tags por conveniencia local.
- Escribir en bronce desde un notebook didáctico.
- Mezclar plata y oro en el mismo bucket InfluxDB.

### Errores comunes

1. Bronce → plata sin pasar por `validate_canonical_tags()`.
2. Crear features (oro) que escriben en plata.
3. Llamar "oro" a un CSV intermedio sin Features Store.

### Checklist específico

- [ ] Cada notebook declara su capa Medallion en sec 5.
- [ ] Los 02_bronze_to_silver_*.ipynb respetan el schema canónico.
- [ ] Los 03_features_*.ipynb generan oro reutilizable.

### Notebooks relacionados

| Capa | Notebooks (count) | Score medio |
|---|---|---|
| Transversal (overview) | 3 | 6.90 |
| Bronce → Plata (`02_bronze_to_silver_*`) | 5 (B, C, D, E + ?) | ~6.5 |
| Plata → Oro (`03_features_*`) | 5 (B, C, D, E, parcialmente F) | ~6.7 |
| Oro (`04_*`, `05_*`) | resto | variable (3.5–9.5) |

### Gaps detectados

- Faltaría un notebook **transversal** sobre **escritura plata→oro vía Flux Tasks**.
- La separación "qué es plata vs oro" no siempre es nítida en notebooks 03_features_*.

---

## 4. Forecasting — series temporales

**Score medio temática:** 6.02 / 10 (Caso B · 5 notebooks).

### Qué debe enseñar

- Estacionariedad (ADF, KPSS).
- ACF / PACF para detectar lags.
- Descomposición additiva / multiplicativa.
- SARIMA(p,d,q)(P,D,Q)_s.
- Baselines obligatorios: `naive_persistence_24h`, `climatology_by_hour`.
- TimeSeriesSplit (NO shuffle).
- Walk-forward con re-entrenamiento.
- IC bootstrap 95% en errores.

### Qué NO debe hacer

- Aplicar `train_test_split(shuffle=True)` a series temporales.
- Reportar MAE sin compararlo con baseline.
- LSTM antes de SARIMA (NA-E).
- Predecir `Ĉ(t)` cuando se promete `Ĉ(t+15)`.

### Errores comunes

1. Leakage: feature en `t` derivada de `t+1`.
2. Olvidar `freq` del DatetimeIndex → resampling buggy.
3. Outliers no tratados → SARIMA explota.

### Checklist específico

- [ ] ADF + ACF antes de SARIMA.
- [ ] 3 baselines comparables (naive_24h, climatología, SARIMA).
- [ ] `TimeSeriesSplit(5)`.
- [ ] IC bootstrap reportado.
- [ ] Métricas por horizonte (1h, 6h, 12h, 24h).

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `02_case_B/01_eda_consumo_electrico` | 7.0 | OK |
| `02_case_B/04_baseline_sarima_xgboost_lstm` | 5.5 | NEEDS_REWRITE |
| `02_case_B/05_validacion_modelo_24h` | 5.3 | NEEDS_REWRITE |
| `05_case_E/04_prediccion_solar` | 8.6 | OK |
| `10_case_J/04_integracion_meteo_trafico` | 8.5 | OK |

### Gaps detectados

- B·04 promete LSTM pero no lo implementa (NA-D).
- B·05 medía pred puntual (Sprint 1 fix pendiente verificar).
- E·04 ya es Top-5: replicar disciplina a B·04 / B·05.

---

## 5. HVAC anomalies — detección de averías físicas

**Score medio temática:** 7.00 / 10 (Caso C · 5 notebooks).

### Qué debe enseñar

- 4 tipos de fallo HVAC (`valve_stuck`, `sensor_drift`, `fan_failure`, `refrigerant_low`).
- Firmas físicas distinguibles (ΔT, duty cycles, ratio fan/valve).
- Rule-based como baseline (regla física bate a ML 70% del tiempo).
- Isolation Forest (anomalía global).
- Autoencoder entrenado **solo con normales** (anomalía local).
- Matriz coste-sensible (FN(`refrigerant_low`) = 1 800 €).

### Qué NO debe hacer

- Train ≡ test (P0-2 original, resuelto Sprint 1).
- AE entrenado con anomalías presentes (segundo leakage).
- Threshold ad-hoc sin validar.
- F1 sin separar por tipo de fallo.

### Errores comunes

1. Usar `iso.fit(X); iso.score_samples(X)` (mismo X).
2. Reportar AUC global cuando los tipos están desbalanceados.
3. Olvidar `class_weight` en clasificación supervisada.

### Checklist específico

- [ ] Split temporal (train antes de test).
- [ ] AE solo con normales en train.
- [ ] Recall por tipo de fallo.
- [ ] Matriz coste-sensible.
- [ ] 4 baselines (rule-based, z-score rolling, IF, AE).

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `03_case_C/01_eda_hvac_fdd` | 7.5 | OK |
| `03_case_C/04_isolation_forest_autoencoder` | 9.0 | OK (Top-2) |
| `03_case_C/05_validacion_fallos_etiquetados` | 5.0 | NEEDS_REWRITE |

### Gaps detectados

- C·05 no aplica matriz coste-sensible documentada en C·04.
- Falta análisis de **tiempo entre fallos** (MTBF) operativo.

---

## 6. IAQ + Occupancy — calidad aire e inferencia ocupación

**Score medio temática:** 6.90 / 10 (Caso D · 5 notebooks).

### Qué debe enseñar

- Balance de masa CO₂ (Wang 2017): `dC/dt ∝ N(t)`.
- IAQ index según EN 16798-1 (categorías I/II/III/IV).
- Ocupación inferida sin sensor de presencia.
- Histéresis L1/L2/L3 en alarmas (5 min sostenido + banda 75 ppm rearme).
- Threshold trivial vs balance físico vs RandomForest.

### Qué NO debe hacer

- Mock 7 días con split 70/30 → test sin clase positiva (P0-1, resuelto).
- Alertas sin histéresis → fatiga de alarmas → operador desactiva.
- Asumir `dCO2/dt > 15 ppm/min` sin calibrar para AULA01.

### Errores comunes

1. Resampling sin documentar: 1min → 15min con `mean()` vs `last()`.
2. CO₂ < 350 ppm (físicamente imposible) sin filtrar.
3. Histéresis con banda muy estrecha (< 50 ppm) → oscilación.

### Checklist específico

- [ ] `assert y_te.sum() > 0` blindado.
- [ ] `class_weight='balanced'`.
- [ ] `TimeSeriesSplit(5)`.
- [ ] Histéresis L1/L2/L3 documentada.
- [ ] EN 16798 citada.

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `04_case_D/01_eda_iaq_ocupacion` | 7.0 | OK |
| `04_case_D/04_modelo_ocupacion_desde_ambiente` | 9.5 | **OK (Top-1)** |
| `04_case_D/05_validacion_iaq_confort` | 4.5 | NEEDS_REWRITE |

### Gaps detectados

- D·05 originalmente 0 alertas (sin histéresis); pendiente verificar fix Sprint 2.
- Falta cobertura de **CO₂ generation rate ASHRAE** (4.5 L/min adulto sentado).

---

## 7. Weather + Solar — meteorología y producción fotovoltaica

**Score medio temática:** 6.63 / 10 (Caso E · 4 notebooks).

### Qué debe enseñar

- Geometría solar (declinación δ, ángulo zenital θ_z).
- Clear-sky model: $G_{clear}(t) = G_{sc} \cdot \cos(\theta_z(t))$.
- Clear-sky index $k_c = G_h / G_{clear} \in [0, 1]$.
- ERA5 conversiones (K → °C, J/m² → W/m², m → mm).
- 4 baselines (climatología, persistencia 1h, clear-sky, RF).
- Skill score: $SS = 1 - MAE_{model} / MAE_{baseline}$.

### Qué NO debe hacer

- Modelar GHI directamente sin descomponer en clear-sky × $k_c$.
- Olvidar máscara nocturna (GHI ≡ 0).
- Olvidar `clip(0)` (predicciones negativas físicamente imposibles).

### Errores comunes

1. Comparar con baseline trivial cuando climatología es mucho más fuerte.
2. Predicción horaria sin ajustar por declinación estacional.
3. Mezclar GHI / DNI / DHI sin distinguir.

### Checklist específico

- [ ] Conversión K → °C documentada.
- [ ] Clip a 0 + máscara nocturna.
- [ ] Climatología por hora como baseline.
- [ ] Skill score reportado.

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `05_case_E/01_eda_era5` | 6.0 | NEEDS_REFACTOR |
| `05_case_E/04_prediccion_solar` | 8.6 | **OK (Top-4)** |

### Gaps detectados

- E·01 promete patrones diurnal/anual pero no aplica descomposición de Iqbal.
- Falta cobertura de **PV system efficiency curve** para producción real.

---

## 8. MLOps — MLflow, lakeFS, reproducibilidad

**Score medio temática:** 6.07 / 10 (Caso F · 3 notebooks).

### Qué debe enseñar

- Naming convention: `^case_[A-J]_(baseline|prod)_\d{4}$`.
- `mlflow.log_params`, `log_metric`, `log_artifact`.
- Tagging lakeFS (`mlflow.set_tag('lakefs_tag', '...')`).
- Determinismo: `seed=42` + `OMP_NUM_THREADS=1`.
- Hash dataset + hash modelo para auditoría EU AI Act.

### Qué NO debe hacer

- Trackear sin tracking_uri configurado (P0-3 original).
- Loggear métricas con nombres no normalizados.
- Olvidar serializar el `requirements.txt` del run.

### Errores comunes

1. `mlflow.disable_system_metrics_logging()` no llamado → ruido.
2. `nested=True` mal usado en runs hijos.
3. Artefactos > 100 MB que rompen S3.

### Checklist específico

- [ ] `mlflow>=2.18` en `[dependency-groups.notebooks]`.
- [ ] `tracking_uri="sqlite:///mlruns.db"` para offline.
- [ ] Run name con la convención CAPTIA.
- [ ] Tag lakeFS presente.

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `06_case_F/01_mlflow_lakefs_overview` | 5.0 | NEEDS_REWRITE |
| `06_case_F/02_tracking_experimentos` | 6.6 | NEEDS_REFACTOR |
| `06_case_F/03_reproducibilidad_datasets_modelos` | 6.6 | NEEDS_REFACTOR |

### Gaps detectados

- F·01 con 0 líneas de código MLflow ejecutable (Sprint 1 fix parcial).
- Falta cobertura de **MLflow Model Registry** (staging/production transitions).

---

## 9. Data Quality — agentes y reglas

**Score medio temática:** 6.40 / 10 (Caso G · 4 notebooks).

### Qué debe enseñar

- Reglas por capa Medallion:
  - **Bronce**: estructura + tipos.
  - **Plata**: schema CAPTIA + completitud + 5 tags + `value` único.
  - **Oro**: KL divergence train vs prod.
- Severidad (warning / blocking).
- Acción recomendada (alert Slack, block deploy).
- Agentes especialistas con tools tipadas.

### Qué NO debe hacer

- KL `density=True` (B6, resuelto Sprint 1) → KL negativos imposibles.
- `evaluate_chatbot_response` comparando con `question` (P0-5, resuelto Sprint 1).
- Hardcodear respuestas en tools.

### Errores comunes

1. KL con bins distintos en train vs prod.
2. Asumir distribución gaussiana para test estadístico.
3. Reglas oro que no detectan drift sutil.

### Checklist específico

- [ ] KL ≥ 0 (assertion).
- [ ] Bins compartidos train/prod.
- [ ] Tools con docstring + type hints.
- [ ] Reglas con severidad explícita.

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `07_case_G/01_reglas_calidad_bronce` | 7.0 | OK |
| `07_case_G/02_reglas_calidad_plata_influxdb` | 4.5 | NEEDS_REWRITE |
| `07_case_G/03_reglas_calidad_oro_ml` | 7.0 | OK |
| `07_case_G/04_agentes_especialistas_calidad` | 7.1 | OK |

### Gaps detectados

- G·02 esqueleto en modo offline.
- Falta cobertura de **continuous validation** (Great Expectations / Deequ).

---

## 10. RAG / Agents — chatbot operativo

**Score medio temática:** 6.16 / 10 (Caso H · 5 notebooks).

### Qué debe enseñar

- Tools (datos numéricos exactos InfluxDB) vs RAG (conocimiento documental).
- TF-IDF español: Recall@k + MRR sobre golden set.
- Routing por keywords + fallback LLM.
- Evaluación con expected_keywords (no solo similarity).
- Tools tipadas: `compare_periods`, `query_avg_co2`, `forecast_consumption`.

### Qué NO debe hacer

- Indexar series temporales como texto.
- Devolver respuestas sin trazabilidad de fuente.
- Tools que devuelven dicts hardcoded.

### Errores comunes

1. Embeddings generados con modelo distinto entre indexing y query.
2. Chunk size > 512 tokens → contexto LLM saturado.
3. Top-k muy alto → ruido en respuesta.

### Checklist específico

- [ ] Golden set con expected_keywords.
- [ ] Recall@3 + MRR reportados.
- [ ] Routing accuracy ≥ 75%.
- [ ] Trazabilidad fuente en cada respuesta.

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `08_case_H/01_arquitectura_rag_tools` | 5.0 | NEEDS_REWRITE |
| `08_case_H/02_tools_influxdb` | 6.5 | NEEDS_REFACTOR |
| `08_case_H/03_mock_tools_modelos_predictivos` | 4.8 | NEEDS_REWRITE |
| `08_case_H/04_rag_documental` | 8.7 | **OK (Top-3)** |
| `08_case_H/05_evaluacion_chatbot` | 5.8 | NEEDS_REFACTOR |

### Gaps detectados

- H·01 conceptual sin tabla decisional (¿cuándo tools vs cuándo RAG?).
- H·03 mocks demasiado triviales (sin estacionalidad).
- Falta cobertura de **LLM-as-judge** para evaluación end-to-end.

---

## 11. Spark vs Pandas — big data y motores

**Score medio temática:** 5.75 / 10 (Caso I · 4 notebooks).

### Qué debe enseñar

- Cuándo Spark NO es necesario (CAPTIA hoy: 38M filas/año).
- Polars 7.3× más rápido que pandas en groupby+mean a 1M filas.
- DuckDB gana a partir de 5M con SQL complejo.
- Spark startup ~1.5 s — no se amortiza para CAPTIA.
- Decisión defensiva: tabla 4 escenarios (5M / 38M / 53M / 500M).

### Qué NO debe hacer

- Justificar Spark sin medir (NA-C: tabla "BDG2 53M" fabricada).
- Comparar Spark single-node con pandas (no es justo).
- Olvidar warmup en benchmarks.

### Errores comunes

1. Comparar pandas a 100k filas con Spark (Spark pierde por startup).
2. No fijar `OMP_NUM_THREADS=1` para benchmarks reproducibles.
3. Mezclar latencia con throughput.

### Checklist específico

- [ ] Warmup explícito (5 runs, mediana, MAD).
- [ ] Misma operación en pandas, polars, duckdb.
- [ ] Spark NO se mide si no aporta (Caso I·03).

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `09_case_I/01_bdg2_overview` | 6.5 | NEEDS_REFACTOR |
| `09_case_I/02_benchmark_pandas` | 6.5 | NEEDS_REFACTOR |
| `09_case_I/03_benchmark_spark` | 3.5 | **NEEDS_REWRITE** (Sprint 2: recomendación honesta) |
| `09_case_I/04_comparativa_resultados` | 6.5 | NEEDS_REFACTOR |

### Gaps detectados

- I·03 reescrito a "NO migrar a Spark hoy" — bien.
- Falta cobertura de **Polars LazyFrame** + `streaming` engine.

---

## 12. YOLO / Traffic — visión artificial

**Score medio temática:** 5.75 / 10 (Caso J · 4 notebooks).

### Qué debe enseñar

- Captura DGT con APScheduler + retry exponencial.
- RGPD: blur sobre matrículas.
- Mock determinista con SHA-256 (no JPEG magic).
- YOLOv8n confidence threshold (0.4 / 0.5 / 0.7).
- Trazabilidad imagen → conteo (timestamp, camera_id).

### Qué NO debe hacer

- `image_bytes[:4]` como seed (B4: JPEG magic común).
- `fake_jpeg` con `rng` interno (B5: imágenes idénticas).
- Predecir `Ĉ(t)` cuando se promete `Ĉ(t+15)` (P0-4).

### Errores comunes

1. Capturar sin retry → packet loss invisible.
2. Olvidar versionado de imágenes (lakeFS / DVC).
3. confidence_threshold muy bajo → falsos positivos.

### Checklist específico

- [ ] SHA-256 hash completo, no magic bytes.
- [ ] Target con shift correcto.
- [ ] RGPD blur documentado.
- [ ] Mock con DGP no trivial.

### Notebooks relacionados

| Notebook | Score | Estado |
|---|---|---|
| `10_case_J/01_captura_imagenes_dgt` | 4.5 | NEEDS_REWRITE |
| `10_case_J/02_inferencia_yolo` | 3.5 | NEEDS_REWRITE |
| `10_case_J/04_integracion_meteo_trafico` | 8.5 | **OK (Top-5)** |

### Gaps detectados

- J·01 promete cron/APScheduler/retry y no entrega.
- J·02 mock determinista pendiente verificar Sprint 1.

---

## 13. Realismo físico — cross-case

**Score medio temática:** transversal a B/C/D/E/J.

### Qué debe enseñar

- Balance de masa CO₂.
- Leyes ASHRAE 62.1 (ventilación) y EN 16798 (IAQ index).
- Geometría solar (declinación, ángulo zenital).
- Histéresis en alarmas.
- Anti short-cycle HVAC (min on/off ≥ 5 min).
- Setpoint jitter realista (std ≤ 0.05 °C).

### Qué NO debe hacer

- Generar CO₂ < 350 ppm (físicamente imposible).
- Predicciones de irradiancia negativas.
- Setpoints que oscilan 75 ev/h (H-23 original).
- Histéresis con banda < 50 ppm.

### Errores comunes

1. ΔT supply-return < 0 sin justificación.
2. Cooling sin deshumidificación implícita.
3. Mocks con correlación tautológica (J: vehicle_count → congestion).

### Checklist específico

- [ ] Rangos físicos validados con assertion.
- [ ] Histéresis documentada con banda numérica.
- [ ] Anti short-cycle min on/off ≥ 5 min.
- [ ] Setpoint jitter std ≤ 0.05 °C.

### Notebooks relacionados

Todos los notebooks de C, D, E, J + parcialmente B. Ver
[`docs/audit/PHYSICAL_REALISM_REPORT.md`](../PHYSICAL_REALISM_REPORT.md) para
score físico estimado 0.94.

### Gaps detectados

- L-PV-02 (cooling deshum) cableada vía Sprint 1; live E2E pendiente.
- Falta documentar **PV system efficiency curve** en Caso E.
- L-PV-09 (jitter setpoint) resuelto Sprint 1 (PATCH 002).

---

## Resumen ejecutivo de la revisión temática

### Score por temática (descendente)

| Temática | Score medio | Notebooks | Prioridad |
|---|---|---|---|
| HVAC anomalies | 7.00 | 5 | P2 (mantener Top-2) |
| IAQ + Occupancy | 6.90 | 5 | P1 (Top-1 + arreglar D·05) |
| Weather + Solar | 6.63 | 4 | P2 |
| Data Quality + Agents | 6.40 | 4 | P1 (G·02) |
| InfluxDB / Flux | 6.40 | 4 | P1 (H·02 verificar) |
| RAG / Chatbot | 6.16 | 5 | P1 (H·01, H·03) |
| MLOps | 6.07 | 3 | P1 (F·01) |
| Forecasting | 6.02 | 5 | P1 (B·04, B·05) |
| Pipeline IoT | 5.93 | 3 | P1 (A·02 verificar) |
| Spark vs Pandas | 5.75 | 4 | P1 (I·03 reescrito) |
| YOLO / Traffic | 5.75 | 4 | P1 (J·01, J·02) |
| Medallion (transversal) | n/a | 45 | P2 (mejorar 02_bronze_to_silver) |
| Realismo físico (cross) | n/a | C, D, E, J | P2 |

### Recomendación final

1. **Bottom-3 temáticas** (5.75–5.93): Pipeline IoT, Spark, YOLO requieren refactor en sus notebooks débiles.
2. **Top-3 temáticas** (≥ 6.63): HVAC, IAQ, Weather muestran el patrón a replicar.
3. **Cohesión cross-case**: Realismo físico debe documentarse mejor en notebooks 03_features_*.
4. **Onboarding interno**: usar Top-3 (D·04, C·04, H·04, E·04, J·04) como **patrón corporativo** para nuevos notebooks.

---

## Referencias

- Auditoría base: [`../NOTEBOOK_AUDIT_DETAILED.md`](../NOTEBOOK_AUDIT_DETAILED.md)
- Auditoría deep-9: [`../NOTEBOOK_AUDIT.md`](../NOTEBOOK_AUDIT.md)
- Realismo físico: [`../PHYSICAL_REALISM_REPORT.md`](../PHYSICAL_REALISM_REPORT.md)
- Matriz casos de uso: [`../USE_CASE_MATRIX.md`](../USE_CASE_MATRIX.md)
- Plan refactor: [`NOTEBOOK_REFACTOR_PLAN.md`](NOTEBOOK_REFACTOR_PLAN.md)
- Guidelines: [`CAPTIA_NOTEBOOK_GUIDELINES.md`](CAPTIA_NOTEBOOK_GUIDELINES.md)
