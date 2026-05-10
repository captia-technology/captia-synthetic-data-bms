# Plan de refactor — 45 notebooks en 3 olas

> **Última verificación:** 2026-05-10
> **Fuente:** [`NOTEBOOK_QUALITY_MATRIX.md`](NOTEBOOK_QUALITY_MATRIX.md) + [`reviews/`](reviews/) + [`NOTEBOOK_AUDIT_DETAILED.md`](../NOTEBOOK_AUDIT_DETAILED.md).
> **Decisión usuario:** refactor **45/45** (no solo bottom-10).
> **Branch sugerido:** `refactor/notebooks-audit-2026-05-10`.

Plan priorizado en **3 olas** según el score actual de cada notebook.
Cada ola incluye un objetivo de score, esfuerzo estimado y catálogo de
cambios típicos. La ejecución sigue el orden:

```
Ola-1 (bottom-10) → execute → test → ruff
Ola-2 (middle-25) → execute → test → ruff
Ola-3 (top-10)    → execute → test → ruff
Validación final 45/45 + REFACTOR_EXECUTION_REPORT.md
```

---

## Ola-1 — Bottom-10 (~14 h)

| # | Notebook | Score | Objetivo | Bug raíz | Cambios típicos |
|---|---|---|---|---|---|
| 1 | `09_case_I/03_benchmark_spark` | 3.5 | ≥ 7.5 | B7 (Sprint 2 fix parcial) | Verificar reescritura "NO Spark hoy" + tabla 4 escenarios |
| 2 | `10_case_J/02_inferencia_yolo` | 3.5 | ≥ 7.5 | B4 (Sprint 1 fix) | Verificar SHA-256 + 5 imágenes con outputs distintos |
| 3 | `04_case_D/05_validacion_iaq_confort` | 4.5 | ≥ 7.5 | 0 alertas, sin histéresis | Histéresis L1/L2/L3 + 5 min sostenido + banda 75 ppm |
| 4 | `07_case_G/02_reglas_calidad_plata_influxdb` | 4.5 | ≥ 7.5 | Esqueleto offline | Reglas Flux mockeadas + visualización + assertions |
| 5 | `10_case_J/01_captura_imagenes_dgt` | 4.5 | ≥ 7.5 | B5 (Sprint 1 fix) | APScheduler real + retry tenacity + RGPD blur |
| 6 | `08_case_H/03_mock_tools_modelos_predictivos` | 4.8 | ≥ 7.5 | Mocks triviales | Estacionalidad diurnal + p10/p50/p90 |
| 7 | `06_case_F/01_mlflow_lakefs_overview` | 5.0 | ≥ 7.5 | 0 código MLflow ejecutable | `tracking_uri="sqlite:///mlruns.db"` + 3 runs ejemplo |
| 8 | `08_case_H/01_arquitectura_rag_tools` | 5.0 | ≥ 7.5 | Conceptual sin tabla decisional | Tabla "tools vs RAG" + ejemplos de routing |
| 9 | `03_case_C/05_validacion_fallos_etiquetados` | 5.0 | ≥ 7.5 | Train ≡ test (Sprint 1 fix) | Verificar split temporal + matriz coste-sensible |
| 10 | `02_case_B/05_validacion_modelo_24h` | 5.3 | ≥ 7.5 | Pred puntual no forecast 24h | Walk-forward 24h + métricas por horizonte 1h/6h/12h/24h |

### Catálogo Ola-1: cambios técnicos

| Notebook | Cambios concretos | Líneas estimadas |
|---|---|---|
| I·03 | Tabla decisional 5M/38M/53M/500M filas; benchmark medido pandas vs polars vs duckdb (NO Spark); recomendación "no migrar hoy" | ~80 |
| J·02 | `hashlib.sha256(image_bytes).digest()[:4]` en `count_vehicles_mock`; assert imágenes ≠ entre sí; 5 outputs visuales | ~60 |
| D·05 | Histéresis L1/L2/L3 con 5 min sostenido + banda 75 ppm; alertas/día; coste evitado 1 050 €/año (baseline §2.2) | ~120 |
| G·02 | Reglas Flux mockeadas (5 tags + value único + completitud); fallback offline con visualización ASCII | ~100 |
| J·01 | APScheduler con `IntervalTrigger(minutes=15)`; tenacity retry exponential backoff; cv2.GaussianBlur sobre ROI | ~150 |
| H·03 | Mock con estacionalidad `sin(2π·hour/24)` + ruido AR(1); cuantiles p10/p50/p90 | ~80 |
| F·01 | `mlflow.set_tracking_uri("sqlite:///mlruns.db")`; 3 runs con `mlflow.start_run(run_name=...)`; assertion runs creados | ~100 |
| H·01 | Tabla "tipo de pregunta → backend" (numérica → tools, normativa → RAG, mixta → híbrido); 5 ejemplos | ~70 |
| C·05 | `train_test_split` temporal estricto; matriz coste-sensible con FN/FP por tipo de fallo; Recall por tipo | ~90 |
| B·05 | Walk-forward 24h con `model.fit()` + `model.predict(horizon=24)`; métricas por horizonte; tabla MAE_h vs h | ~110 |

### Verificación Ola-1

```bash
# Por notebook
for nb in $(cat ola1.txt); do
  uv run python scripts/execute_notebooks.py --notebook "$nb" --timeout 300
  uv run pytest tests/integration/test_notebooks_integrity.py -k "$(basename $nb .ipynb)"
done

# Update matrix
uv run python scripts/audit_notebooks.py --matrix --status

# Score check
uv run python scripts/audit_notebooks.py --bottom 10 --threshold 7.5
```

---

## Ola-2 — Middle-25 (~18 h)

Notebooks con score 5.5-7.5 que requieren **refinamiento** (no reescritura).

### Catálogo Ola-2: 25 notebooks

| # | Notebook | Score actual | Objetivo | Foco principal |
|---|---|---|---|---|
| 1 | `02_case_B/04_baseline_sarima_xgboost_lstm` | 5.5 | 8.5 | Cohesión LaTeX↔código + LSTM honest |
| 2 | `08_case_H/05_evaluacion_chatbot` | 5.8 | 8.5 | Sprint 1 fix B3 verificado + 5 ejemplos golden set |
| 3 | `01_case_A/03_validacion_telegraf_influx_grafana` | 5.3 | 8.0 | Tabla troubleshooting (8 rows) |
| 4 | `05_case_E/03_features_meteorologicas` | 5.9 | 8.0 | Conexión LaTeX clear-sky↔código |
| 5 | `01_case_A/02_publicacion_mqtt_a_influxdb` | 6.0 | 8.0 | Sec 19 LaTeX queueing → calcular ρ y λ |
| 6 | `02_case_B/02_bronze_to_silver_energy` | 6.0 | 8.0 | Schema validation + helper reuse |
| 7 | `05_case_E/01_eda_era5` | 6.0 | 8.0 | Geometría solar implementada (no solo citada) |
| 8 | `05_case_E/02_bronze_to_silver_weather` | 6.0 | 8.0 | Conversiones K→°C documentadas con assertion |
| 9 | `08_case_H/02_tools_influxdb` | 6.5 | 8.5 | Sprint 1 fix B1 verificado + 5 tools tipadas |
| 10 | `04_case_D/02_bronze_to_silver_iaq` | 6.5 | 8.0 | `validate_canonical_tags()` aplicado |
| 11 | `02_case_B/03_features_forecasting` | 6.5 | 8.0 | `is_lectivo` calendario CV documentado |
| 12 | `09_case_I/01_bdg2_overview` | 6.5 | 8.0 | NA-C: tabla "BDG2 53M" honesta |
| 13 | `09_case_I/02_benchmark_pandas` | 6.5 | 8.0 | Warmup + mediana + MAD |
| 14 | `09_case_I/04_comparativa_resultados` | 6.5 | 8.0 | Reusar Sprint 2 reescritura I·03 |
| 15 | `00_overview/02_conexion_influxdb_y_variables_entorno` | 6.5 | 8.0 | Fallback offline visualizado |
| 16 | `06_case_F/02_tracking_experimentos` | 6.6 | 8.0 | Verificar mlflow runs tras Sprint 1 |
| 17 | `06_case_F/03_reproducibilidad_datasets_modelos` | 6.6 | 8.0 | Hash datasets + hash modelo + seed |
| 18 | `03_case_C/03_features_anomalias_hvac` | 6.7 | 8.0 | NA-H: errores vs propio código (valve_duty_60 sin shift) |
| 19 | `03_case_C/02_bronze_to_silver_hvac` | 6.8 | 8.0 | Etiquetas en `captia_fault_labels` separadas |
| 20 | `00_overview/01_schema_captia_influxdb` | 7.0 | 8.5 | Profundizar buckets + retention policy |
| 21 | `02_case_B/01_eda_consumo_electrico` | 7.0 | 8.5 | Sprint 3 fix ADF/ACF verificado + 4-panel diagnostic |
| 22 | `04_case_D/01_eda_iaq_ocupacion` | 7.0 | 8.5 | dCO2/dt como predictiva + visualización |
| 23 | `04_case_D/03_features_confort_ocupacion` | 7.0 | 8.5 | EN 16798 categorías I/II/III/IV documentadas |
| 24 | `07_case_G/01_reglas_calidad_bronce` | 7.0 | 8.5 | Reglas sobre CSV originales (BDG2, In-Gauge, LBNL) |
| 25 | `07_case_G/03_reglas_calidad_oro_ml` | 7.0 | 8.5 | Sprint 1 fix B6 verificado + threshold operativo |

### Catálogo Ola-2: cambios típicos

- **Cohesión LaTeX↔código (sec 19)**: la fórmula citada coincide con código de secs 14-15. Si SARIMA(2,0,2)(1,1,1)_24 está en sec 19, debe estar en `SARIMAX(...)` en sec 14.
- **ROI auditable (sec 20)**: cita línea exacta de `economic_baseline.md`.
- **Visualizaciones diagnostic**: añadir `plot_regression_diagnostic()` o `plot_classification_diagnostic()` donde falte.
- **Bibliografía con DOI** cuando exista (NA-NC: no inventar).
- **Helper reuse**: aplicar `eval_helpers` y `diagnostic_plots` (NA-B).

### Verificación Ola-2

```bash
uv run python scripts/audit_notebooks.py --matrix --status
# Esperado: score medio ≥ 8.0 sobre middle-25
```

---

## Ola-3 — Top-10 (~8 h)

Notebooks con score ≥ 8.0 que requieren **pulido**.

### Catálogo Ola-3: 10 notebooks

| # | Notebook | Score actual | Objetivo | Pulido |
|---|---|---|---|---|
| 1 | `04_case_D/04_modelo_ocupacion` | 9.5 | 9.5 | Mantener — replicar disciplina al resto |
| 2 | `03_case_C/04_isolation_forest_autoencoder` | 9.0 | 9.0 | Mantener — añadir matriz coste-sensible cross-link |
| 3 | `08_case_H/04_rag_documental` | 8.7 | 9.0 | Verificar secs 19/20/21 completas |
| 4 | `05_case_E/04_prediccion_solar` | 8.6 | 9.0 | Cohesión LaTeX clear-sky |
| 5 | `10_case_J/04_integracion_meteo_trafico` | 8.5 | 9.0 | Sprint 1 fix verificado + ablation explícita |
| 6 | `03_case_C/01_eda_hvac_fdd` | 7.5 | 8.5 | 4 firmas físicas con plots |
| 7 | `00_overview/00_arquitectura_medallion_captia` | 7.2 | 8.5 | Mermaid mejorado + ejemplos cross-case |
| 8 | `07_case_G/04_agentes_especialistas_calidad` | 7.1 | 8.5 | Sprint 1 fix P0-5 verificado |
| 9 | `00_overview/01_schema_captia_influxdb` | 7.0 | 8.5 | (cubierto en Ola-2) |
| 10 | `02_case_B/01_eda_consumo_electrico` | 7.0 | 8.5 | (cubierto en Ola-2) |

### Catálogo Ola-3: pulido

- **Ejercicios con rúbrica** (criterio cuantitativo de aceptación).
- **Mini-conclusiones por sección** (≥ 150 chars cada una).
- **Errores comunes (sec 17)** con ≥ 3 entradas específicas.
- **Bibliografía con DOI/URL** completa.
- **Cross-links** entre notebooks (D·04 ↔ C·04 patrón Top-2).

### Verificación Ola-3

```bash
uv run python scripts/audit_notebooks.py --matrix --status
# Esperado: top-10 todos ≥ 8.5; D·04 y C·04 ≥ 9.0
```

---

## Plantilla de cambio por notebook

Para cada notebook refactorizado, documentar:

```yaml
notebook: notebooks/<case>/<NN_name>.ipynb
current_state:
  score: <X.Y>
  bugs: [<lista de P0/P1>]
  issues: [<lista NA-* aplicables>]
target_state:
  score: <X.Y>
  veredicto: <A|B|C|D|E>
changes:
  - "Cambio 1 con líneas concretas (sec 14, fila 5: ...)"
  - "Cambio 2"
estimated_complexity: <bajo|medio|alto>
dependencies:
  - <notebook predecesor / helper requerido>
validation:
  - "uv run python scripts/execute_notebooks.py --notebook <path>"
  - "uv run pytest tests/integration/test_notebooks_integrity.py -k <name>"
priority: <P0|P1|P2>
```

---

## Reglas de oro durante el refactor

1. **Un notebook a la vez**. No abrir 5 PRs simultáneos.
2. **Backup**: branch `refactor/notebooks-audit-2026-05-10` con commits granulares.
3. **No mezclar**: si el cambio es sustancial (Ola-1) → un commit por notebook. Cambios de estilo agrupables en commit aparte.
4. **Builder edits preferred**: editar `scripts/build_notebooks/case_*.py` en lugar de `.ipynb` directo. Determinismo preservado.
5. **Tras cada notebook**:
   - `uv run python -m scripts.build_notebooks` (regenerar `.ipynb`).
   - `uv run python scripts/execute_notebooks.py --notebook <path> --timeout 300`.
   - `uv run pytest tests/integration/test_notebooks_integrity.py -k <name>`.
   - `uv run python scripts/audit_notebooks.py --matrix` (update matriz).
6. **Update STATUS.md** ola por ola.
7. **No commit con `--no-verify`** (regla CLAUDE.md raíz).

---

## Estimación de esfuerzo total

| Ola | Notebooks | Horas | Score objetivo |
|---|---|---|---|
| Ola-1 (bottom-10) | 10 | ~14 h | ≥ 7.5 |
| Ola-2 (middle-25) | 25 | ~18 h | ≥ 8.0 (medio) |
| Ola-3 (top-10) | 10 | ~8 h | ≥ 8.5 (medio) |
| Validación final | 45 | ~3 h | n/a |
| **Total refactor** | 45 | **~43 h** | **≥ 8.5 medio** |

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Refactor rompe dependencias entre notebooks | DAG en `NOTEBOOK_PLAN.md`; refactor en orden topológico |
| Timeout en ejecución (45 nb × hasta 5 min) | `--workers 4` + `--timeout 300` |
| Test integridad falla tras refactor | Reusar template canónico; validar `validate_canonical_tags()` |
| Determinismo perdido | Builder regenera todo; seeds 42 fijas |
| Score no sube al objetivo | Reentrar al notebook con review específico de `reviews/<nb>.md` |
| Stack docker no disponible para tests E2E | Usar `INFLUX_OFFLINE=true` durante refactor; E2E al final |

---

## Criterio de aceptación final

1. **Score medio post-refactor ≥ 8.5/10** (vs 6.31 baseline / 8.1 pre-refactor estimado).
2. **Bottom-10 todos ≥ 7.5**.
3. **Top-10 todos ≥ 8.5**.
4. **45/45 notebooks** ejecutables con outputs persistidos.
5. **270+ tests integridad** PASS.
6. **0 ruff errors**.
7. **mkdocs build --strict** verde.
8. **`REFACTOR_EXECUTION_REPORT.md`** documenta diff por notebook con pre/post score.

---

## Referencias

- Matriz de calidad: [`NOTEBOOK_QUALITY_MATRIX.md`](NOTEBOOK_QUALITY_MATRIX.md)
- Reviews: [`reviews/`](reviews/)
- Auditoría base: [`../NOTEBOOK_AUDIT_DETAILED.md`](../NOTEBOOK_AUDIT_DETAILED.md)
- Auditoría deep-9: [`../NOTEBOOK_AUDIT.md`](../NOTEBOOK_AUDIT.md)
- Plan de uso: [`../NOTEBOOK_PLAN.md`](../NOTEBOOK_PLAN.md)
- Guidelines: [`CAPTIA_NOTEBOOK_GUIDELINES.md`](CAPTIA_NOTEBOOK_GUIDELINES.md)
