# Auditoría extrema de notebooks didácticos

> **Última verificación:** 2026-05-10
> **Auditores:** code-reviewer (×2 agentes paralelos) + lectura directa.
> **Alcance auditado en profundidad:** 9 notebooks representativos
> de los 45 (1-2 por caso, priorizando los notebooks de modelado).
> **Tono:** brutal, constructivo, accionable.

## Veredicto ejecutivo

| Notebook | Score | Estado |
|---|---|---|
| `01_case_A/02_publicacion_mqtt_a_influxdb.ipynb` | **6.6/10** | Aceptable, costuras pedagógicas |
| `02_case_B/04_baseline_sarima_xgboost_lstm.ipynb` | **6.0/10** | Funcional, falta CV / IC |
| `03_case_C/04_isolation_forest_autoencoder.ipynb` | **5.4/10** | Engañoso por leakage train≡test |
| `04_case_D/04_modelo_ocupacion_desde_ambiente.ipynb` | **2.8/10** | **ROTO** — F1=0 en clase |
| `05_case_E/04_prediccion_solar.ipynb` | **4.7/10** | Decorativo, fórmulas desconectadas |
| `06_case_F/02_tracking_experimentos.ipynb` | **3.8/10** | `mlflow disponible: False`; nada se ejecuta |
| `07_case_G/04_agentes_especialistas_calidad.ipynb` | **2.9/10** | **BUG SEMÁNTICO**; funciones hardcoded |
| `08_case_H/04_rag_documental.ipynb` | **5.4/10** | Heatmap útil; faltan secs 19/20/21 |
| `09_case_I/04_comparativa_resultados.ipynb` | **4.1/10** | No mide nada; benchmark inventado |
| `10_case_J/04_integracion_meteo_trafico.ipynb` | **4.5/10** | Probable leakage; target sin lag |

**Score medio:** **4.6 / 10**.
**Por debajo del umbral de "publicable como material oficial del curso".**

> *"Los notebooks tienen huesos buenos (helpers, schema, mocks, bibliografía). El problema no es estructural, es de **completitud y rigor**."*

## Hallazgos transversales

### A. Patrones críticos repetidos

| ID | Patrón | Severidad | Notebooks afectados |
|---|---|---|---|
| **NA-01** | Modelos sin baseline naïf comparable | Crítica | B, C, D, E, F, J |
| **NA-02** | Sin CV temporal (`TimeSeriesSplit`); split 80/20 cronológico simple | Crítica | B, C, D, F, J |
| **NA-03** | LaTeX doctoral *desconectada* del código (decorativa) | Crítica | C, D, E, G, I, J |
| **NA-04** | Sec. 15 lista errores que el propio código comete | Alta | C, D, E, J |
| **NA-05** | Asserts cosméticos (`auc>0.7`, `rmse<250`) sin IC | Alta | C, D, E |
| **NA-06** | ROIs sin denominador / supuestos auditables | Alta | A, C, D, E, F, G, I, J |
| **NA-07** | Visualizaciones decorativas (1 plot por notebook, sin insight) | Alta | A, C, D, E, F, G, I, J |
| **NA-08** | Plantilla de 21 secciones rellenadas con "no aplica" | Media | A, C, D, E, F, G, I |
| **NA-09** | Mocks con DGP no documentado → posible leakage encubierto | Alta | J (vehicle_count→congestion_level corr=0.89) |
| **NA-10** | Setup canónico replicado literalmente (18 líneas × 45 notebooks) | Baja | Todos |

### B. Bloqueantes (P0) — material no publicable hasta resolverse

| ID | Notebook | Problema |
|---|---|---|
| **P0-1** | Caso D · 04 | Ejecuta y reporta `RF F1: 0.0`. Mock 7 días + split 70/30 → test sin clase positiva. El `_warn_prf` salta. **Showstopper pedagógico**: el alumno ve un modelo roto y aprende patrón equivocado. |
| **P0-2** | Caso C · 04 | `iso.fit(X); iso.score_samples(X)`. **Train ≡ test**. Leakage perfecto. AUC dentro-de-muestra (no generaliza). El AE además entrena con anomalías presentes (segundo leakage). |
| **P0-3** | Caso F · 02 | Output ejecutado muestra `mlflow disponible: False`. Cae al fallback JSON. **Todo el contenido MLflow no se ejecuta**. El alumno aprende cero de MLflow real. |
| **P0-4** | Caso J · 04 | `corr(vehicle_count, congestion_level) = 0.89` sugiere `congestion_level = bin(vehicle_count)` en el mock → predicción tautológica. Además el título promete `Ĉ(t+15)` y el código predice `Ĉ(t)`. |
| **P0-5** | Caso G · 04 | `evaluate_chatbot_response` compara `expected` con `question`, no con la respuesta del chatbot. **Bug semántico** que un code review tumbaría. Las 3 "tools" devuelven dicts hardcoded sin tocar datos. |

### C. Alta prioridad (P1) — cuestiones de rigor

| ID | Acción |
|---|---|
| **P1-1** | Conectar fórmulas LaTeX (sec 19) con celdas que las implementen: balance masa CO₂ (D), clear-sky model (E), $N^*$ medido (I), $\hat C(t+15)$ (J), Recall@k (H). |
| **P1-2** | Añadir baselines en B/C/D/E: persistencia 24h, rule-based ΔT, z-score rolling, climatología por hora, threshold físico CO₂>600. |
| **P1-3** | Caso H · 04 le faltan secciones 19/20/21 (rotas vs el resto del curso). |
| **P1-4** | Caso E · 04: aplicar `clip(0)` y máscara nocturna (errores que el propio sec 15 advierte). |
| **P1-5** | Caso I · 04: sustituir el modelo simulado por benchmark real (pandas vs polars vs duckdb vs pyspark local). |
| **P1-6** | Validación cruzada temporal `TimeSeriesSplit(n_splits=5)` en lugar de splits estáticos. |
| **P1-7** | Reportar IC 95% bootstrap para AUC/F1/RMSE en lugar de point estimates. |

### D. Media prioridad (P2) — mejora estructural

| ID | Acción |
|---|---|
| **P2-1** | ROIs auditables: tabla de supuestos con denominador explícito, baseline de coste, sensibilidad ±20%. |
| **P2-2** | Helpers `plot_regression_diagnostic` y `plot_classification_diagnostic` en `notebooks/_common/plotting.py`. |
| **P2-3** | Rúbricas en ejercicios: criterio de aceptación cuantitativo. |
| **P2-4** | Documentar DGP de cada mock en `synthetic_mocks.py` (qué señal tiene, qué leakage no debe suponerse). |
| **P2-5** | Consolidar setup canónico en `notebooks._common.setup.bootstrap()`. |

## Scorecard detallado

| Notebook | Pedag | Código | Rigor | Visu | Ejer | ErrCom | ROI | Reuso | Coher | **Total** |
|---|---|---|---|---|---|---|---|---|---|---|
| A · 02 MQTT→Influx | 6 | 7 | 5 | 4 | 5 | 7 | 5 | 8 | 6 | **6.6** |
| B · 04 SARIMA/XGB/LSTM | 6 | 6 | 5 | 5 | 6 | 7 | 5 | 7 | 6 | **6.0** |
| C · 04 IF+AE | 6 | 4 | 3 | 6 | 6 | 5 | 6 | 6 | 5 | **5.4** |
| D · 04 Ocupación | 4 | 2 | 2 | 3 | 5 | 4 | 5 | 5 | 1 | **2.8** |
| E · 04 Solar | 5 | 5 | 4 | 5 | 5 | 4 | 4 | 5 | 3 | **4.7** |
| F · 02 MLflow tracking | 4 | 3 | 2 | 4 | 3 | 5 | 3 | 5 | 3 | **3.8** |
| G · 04 Agentes calidad | 3 | 2 | 2 | 2 | 3 | 4 | 4 | 3 | 2 | **2.9** |
| H · 04 RAG | 6 | 6 | 4 | 6 | 6 | 6 | 0 | 6 | 4 | **5.4** |
| I · 04 Spark vs pandas | 5 | 2 | 2 | 5 | 5 | 7 | 4 | 4 | 5 | **4.1** |
| J · 04 Tráfico × meteo | 5 | 5 | 3 | 5 | 5 | 5 | 4 | 5 | 5 | **4.5** |

(Pesos: Pedag 15%, Código 20%, Rigor 20%, Visu 10%, Ejer 10%, ErrCom 5%, ROI 5%, Reuso 5%, Coher 10%.)

## Plan de remediación

### Sprint 1 — P0 (4-7 días, esta semana)

1. **Caso D**: aumentar mock a 30 días, `class_weight='balanced'`, `TimeSeriesSplit(5)`, baseline analítico (inversión balance masa CO₂), `assert y_te.sum() > 0`.
2. **Caso C**: `train_test_split` con stratify (o `TimeSeriesSplit`); AE se entrena solo con etiquetas normales; añadir 2 baselines (rule-based ΔT, z-score rolling); reportar F1 y TPR@1%FPR.
3. **Caso F**: añadir `mlflow` al `[dependency-groups.notebooks]` (ya está); verificar que se ejecuta; añadir baseline naïf-24h al run; loggear MAE_naive y MAE_improvement_pct.
4. **Caso J**: regenerar `traffic_camera_mock` con efecto lluvia (-15% vehicle_count cuando precip>2); target lag `y = congestion_level.shift(-15)`; añadir confusion matrix multi-clase.
5. **Caso G**: reescribir `evaluate_chatbot_response(question, answer, expected_keywords)` con overlap real; reescribir `validate_silver_layer(df)` para computar `df.isna().mean()` + range checks.

### Sprint 2 — P1 (2 semanas)

6. **Conectar fórmulas con código** en D, E, I, J, H.
7. **Añadir baselines comparativos** y tabla skill score con IC bootstrap.
8. **Recall@k + MRR** en Caso H · 04.
9. **Visualizaciones diagnósticas estándar** vía helpers.

### Sprint 3 — P2 (mes)

10. **ROIs honestos** con TCO.
11. **Rúbricas en ejercicios**.
12. **Consolidar setup canónico** en helper.

## Lo que SÍ funciona bien (preservar)

- `notebooks/_common/captia_schema.py` y `synthetic_mocks.py` — buen diseño, determinista, reutilizable.
- Política `# MOCK ...` — trazabilidad explícita.
- Setup canónico idéntico → reproducibilidad.
- Bibliografías reales (Liu 2008, Hinton 2006, Iqbal 1983, ASHRAE, EN 16798) → no inventadas.
- Estructura Medallion consistente.
- Notebook A · 02: errores comunes específicos a `paho-mqtt`.
- Notebook H · 04: heatmap `cosine_similarity` aporta insight real.
- Notebook I · 04: errores comunes #3 ("comparar Spark single-node con pandas no es justo") es la mejor advertencia técnica del set.

## Riesgos de despliegue como material lectivo

1. **Caso D ejecuta mostrando F1=0.** Si un alumno lo entrega como TFM, el tribunal lo destrozará. **Bloqueante.**
2. **Asserts laxos** crean falsa sensación de "tests pasando". Con 1M iteraciones del curso, generará alumnos que escriben código verde-pero-incorrecto.
3. **Fórmulas LaTeX presentadas como "doctoral"** sin implementarse: percibido como **marketing académico** por revisor estricto.
4. **ROIs no auditables**: si CAPTIA presenta esto a clientes corporativos, basta una pregunta ("¿cuál es la línea base?") para que se desmorone.

## Conclusión

**Cuatro semanas de trabajo focalizado en P0+P1 llevan los 9 notebooks
auditados de score medio 4.6 → 7+ /10.** Como están ahora, el Caso D es
inentregable y los Casos C/F/G/J tienen problemas de rigor que un revisor
externo señalaría inmediatamente.

El siguiente paso es ejecutar el Sprint 1 (P0) — los 5 fixes son
concretos, acotados y de alto impacto.
