# Guidelines oficiales — Notebooks didácticos CAPTIA

> **Última verificación:** 2026-05-10
> **Estado:** Vinculante para los 45 notebooks del repo.
> **Audiencia:** Equipo CAPTIA Technology, profesorado IES Simarro, integradores CENTINELA+, alumnos del Curso de Especialización IA & Big Data 2025-2026.

Este documento define el **estándar de calidad** que todo notebook
didáctico del proyecto **CAPTIA Synthetic Data BMS** debe cumplir.
Se aplica a los 45 notebooks de `notebooks/{00..10}_*/` y al template
canónico `notebooks/_templates/CAPTIA_NOTEBOOK_TEMPLATE.ipynb`.

La calidad se mide en **3 ejes corporativos** (peso 0.4 / 0.4 / 0.2):

| Eje | Peso | Mide |
|---|---|---|
| **Técnico** | 0.40 | reproducibilidad, validaciones, schema, modelos, métricas, ausencia de leakage |
| **Didáctico** | 0.40 | progresión, contexto, interpretación, ejercicios, errores comunes |
| **Corporativo** | 0.20 | portada homogénea, ROI auditable, alineación CENTINELA+, claridad visual |

---

## Decisión arquitectónica — secs 19/20/21 vs 22

**Decisión 2026-05-10 (Sprint 6.2):** las secciones del bloque apéndice
están repartidas así por motivos pedagógicos:

| Sección | Granularidad | Por qué |
|---|---|---|
| **19. Marco teórico** | **caso** (común a los 5 notebooks del caso) | El alumno necesita una vista teórica unificada del caso B (forecast), no fragmentada en 5 piezas inconexas. Estudiar SARIMA en B·04 sin haber visto la familia completa de modelos en sec 19 es contraproducente. |
| **20. Visión corporativa** | **caso** (común a los 5 notebooks) | El ROI del caso B es un agregado: forecast 24h (~8 064 €/centro/año) no se descompone por etapa de notebook. La cifra es la misma se cite desde 01_eda o 04_baseline. |
| **21. Bibliografía** | **caso** (común a los 5 notebooks) | Las referencias canónicas del caso (Box-Jenkins 1976, Chen-Guestrin 2016, Hochreiter 1997) son las mismas en cualquier etapa. |
| **22. Nota etapa** | **(caso × etapa)** única | Aquí va la diferenciación: cada uno de los 45 notebooks tiene un párrafo único anclado a Simarro/AULA01/CENTINELA+ con cifra Fermi etapa-específica. |

**Esto no es NA-A.** El patrón NA-A original (Sprint 0) era *5 notebooks
del Caso B con apéndices LITERALMENTE idénticos sin valor añadido por la
repetición*. La estructura actual:

- **Diferencia explícitamente** lo que es por-caso (teoría/ROI/biblio) de
  lo que es por-etapa (sec 22 + nota etapa con cifra Fermi).
- **Replica intencionalmente** el bloque del caso para que cualquier
  notebook sea autocontenido al imprimir / leer en aislamiento.
- **Cita el baseline económico** (`baseline_section`) en sec 20
  trazando ROI-etapa al baseline-caso.

Si el alumno descarga `02_case_B/04_baseline_sarima` y lo abre, ve:
- secs 1-18 con la lógica concreta del notebook (modelado SARIMA).
- sec 19/20/21 con la teoría/ROI/biblio del caso completo (B —
  forecasting). Ese alumno NO tiene que abrir los otros 4 notebooks
  para entender la motivación o coste-beneficio.
- sec 22 con la nota etapa específica de modelado (la única parte
  diferente vs los otros 4 notebooks del caso B).

Sprint 6.2 cierra esta cuestión con la decisión consciente:
**arquitectura correcta — no es duplicación, es replicación
intencional**.

---

## 1. Estructura estándar de notebook (22 secciones)

Todos los notebooks **deben** seguir esta estructura. El builder
`scripts/build_notebooks/` y el template
`notebooks/_templates/CAPTIA_NOTEBOOK_TEMPLATE.ipynb` la respetan
literalmente.

```text
0  Cabecera trazable (md)        ← test integridad valida `Caso de uso` / `Capa Medallion` / `Spec:`
1  Portada corporativa
2  Objetivos de aprendizaje
3  Contexto del caso de uso
4  Relación con CENTINELA+
5  Relación con arquitectura Medallion
6  Datos de entrada
7  Setup y variables de entorno   ← SETUP_BLOCK canónico, idéntico en los 45
8  Schema CAPTIA esperado          ← validate_canonical_tags()
9  Carga de datos
10 Validación inicial de datos
11 Exploración didáctica
12 Transformaciones paso a paso
13 Visualizaciones
14 Modelado o análisis             ← baseline → intermedio → final
15 Validación técnica              ← asserts cuantitativos
16 Interpretación de resultados
17 Errores comunes
18 Resumen final + próximos pasos
19 Marco teórico (doctoral)        ← LaTeX
20 Visión corporativa CAPTIA       ← ROI anclado a economic_baseline.md
21 Bibliografía y referencias
22 Etapa del pipeline · {única}    ← _CASE_STAGE_NOTES (45 únicas, anti-NA-A)
```

> **22 secciones, no 21:** las "21 secciones del prompt original" se
> mapean a las 22 actuales — la sección 22 se introdujo en Sprint 4 para
> resolver el patrón **NA-A** (apéndices duplicados dentro del mismo caso).

---

## 2. Portada corporativa

Cada notebook empieza con una portada **markdown** con metadata
trazable. La cabecera (sec 0) la genera
`scripts/_nb_builder.py:header()` y los tests integridad la validan.

### Cabecera mínima (sec 0)

```markdown
# {{TITLE}}

> _Tutorial · Caso de uso: **{{CASE}}** · Capa Medallion: **{{LAYER}}** · Spec: `{{SPEC}}`_

Material docente del proyecto **CAPTIA Synthetic Data BMS** — IES Dr. Lluís Simarro,
Curso de Especialización IA & Big Data 2025-2026.
```

### Portada extendida (sec 1)

```markdown
## 1. Portada corporativa

**Proyecto:** CAPTIA Synthetic Data BMS
**Caso de uso:** {{CASE}}  ← A / B / C / D / E / F / G / H / I / J / Overview
**Capa Medallion:** {{LAYER}}  ← bronce / plata / oro / transversal
**Etapa pipeline:** {{STAGE}}  ← 01-EDA / 02-ETL / 03-Features / 04-Modelado / 05-Validación
**Spec asociada:** `{{SPEC}}`
**Última revisión:** YYYY-MM-DD
**Estado:** Validado / Experimental / Requiere datos reales
**Audiencia:** Alumnos / Data Scientists / Equipo CAPTIA / Cliente técnico
```

### Ejemplo Top-5 — `04_case_D/04_modelo_ocupacion_desde_ambiente`

Score 9.5/10. Cabecera literal:

```markdown
# Modelo de ocupación desde ambiente AULA01

> _Tutorial · Caso de uso: **D** · Capa Medallion: **oro** · Spec: `docs/specs/synthetic-bms/02-domain-spec.md`_
```

Características que ganan score:

- 3 baselines (threshold trivial / balance de masa físico / RandomForest balanceado).
- `TimeSeriesSplit(5)` con `class_weight='balanced'`.
- IC bootstrap 95 % en F1.
- `assert y_te.sum() > 0` blindado contra mock degenerado.

---

## 3. Rigor técnico (17 reglas obligatorias)

| # | Regla | Anti-patrón asociado |
|---|---|---|
| 1 | **No hardcodear secretos** | Tokens InfluxDB / OpenAI inline (`SECRET_PATTERN` en tests) |
| 2 | **No hardcodear paths absolutos** | `'C:/Users/...'`, `'/home/...'` salvo en comentarios |
| 3 | **Usar `.env`** vía `notebooks._common.connection.load_env()` | Lectura directa de `os.environ` sin fallback |
| 4 | **Validar existencia de datos** antes de usarlos | `df.head()` sin `assert len(df) > 0` previo |
| 5 | **Validar schema de entrada** | NO usar `validate_canonical_tags()` cuando aplica |
| 6 | **Validar columnas esperadas** | `df["value"]` sin `assert "value" in df.columns` |
| 7 | **Validar tipos** | Mezclar str/int en `value` |
| 8 | **Validar timestamps** monotónicos | `df.set_index("ts")` sin `is_monotonic_increasing` |
| 9 | **Validar nulos** | Ignorar `df.isna().mean()` |
| 10 | **Validar duplicados** | `(asset_id, variable, ts)` sin dedup |
| 11 | **Validar rangos físicos** | `temperature ∈ [10, 40]`, `co2 ∈ [350, 5000]`, `dt_supply_return ≥ 0` |
| 12 | **Separar real / público / sintético / mock** | Mocks no etiquetados (`# MOCK — sintético` faltante) |
| 13 | **Documentar supuestos** | Asumir estacionariedad sin ADF (NA-D) |
| 14 | **No presentar mocks como resultados reales** | "BDG2 53M filas" en gráfica producida por 100 filas mock (NA-C) |
| 15 | **No entrenar modelos sin baseline** | XGBoost sin `naive_persistence_24h` (NA-E) |
| 16 | **No mostrar métricas sin interpretación** | `print(f"MAE={mae}")` sin sec 16 narrativa |
| 17 | **No usar modelos complejos antes del baseline** | LSTM sin SARIMA → SARIMA sin naive |
| 18 | **Re-ejecutables top→bottom** | Variables creadas en sec 14 usadas en sec 9 |

### Catálogo de validaciones reusables

```python
from notebooks._common.captia_schema import validate_canonical_tags
from notebooks._common.eval_helpers import (
    bootstrap_ci,
    naive_persistence_24h,
    climatology_by_hour,
    occupancy_from_co2_balance,
    hvac_rule_dt_zero,
    rolling_zscore_anomaly,
    time_series_cv_evaluate,
    compare_models,
)
from notebooks._common.diagnostic_plots import (
    plot_regression_diagnostic,
    plot_classification_diagnostic,
    plot_iot_pipeline_diagnostic,
)
```

> **Regla NA-B:** estos helpers existen — usarlos. No reimplementar
> bootstrap, baselines o plots 4-panel a mano.

---

## 4. Rigor didáctico (13 reglas)

| # | Regla | Anti-patrón |
|---|---|---|
| 1 | Introducir el **problema** antes del código | Empezar con `import pandas as pd` |
| 2 | Explicar **por qué** se usa cada técnica | Aplicar IsolationForest sin justificar vs rule-based |
| 3 | Explicar **qué se espera ver** ANTES del plot | Plot sin hipótesis previa |
| 4 | **Interpretar** cada gráfica | Plot sin texto narrativo debajo |
| 5 | Añadir **diagramas Mermaid** cuando ayuden | Texto plano describiendo flujo de 5 etapas |
| 6 | Mini **conclusiones** por sección | Saltar de 11 a 12 sin cierre |
| 7 | Añadir **preguntas de reflexión** | (recomendado en notebooks avanzados) |
| 8 | Añadir **ejercicios opcionales** | Notebook sin sección 17 |
| 9 | Añadir bloque **errores comunes** (sec 17) | Lista vacía o copiada |
| 10 | Bloque **reutilización CENTINELA+** | Sec 18 sin pasos para datos reales |
| 11 | **Evitar celdas enormes** (> 50 líneas) | Cell de 200 líneas con todo el modelado |
| 12 | **Evitar funciones mágicas** sin explicar | `magic_transform(df)` sin docstring |
| 13 | **Evitar saltos conceptuales** | EDA → LSTM sin pasar por baseline |

### Patrón "explica antes, muestra después"

✓ **Correcto:**

```markdown
**Hipótesis:** esperamos un patrón diurnal con pico mañana 08-15h y
valle nocturno 22-08h, ya que `is_lectivo=True` solo en horario escolar.
```

```python
df.groupby(df.index.hour)["power_kw"].mean().plot(...)
```

```markdown
**Lectura del gráfico:** se confirma el patrón esperado; pico a las
12:00 (~3.2 kWh) y valle a las 04:00 (~0.4 kWh). El pico levemente
desplazado vs nuestra hipótesis se debe a recreos y comedor.
```

✗ **Incorrecto:**

```python
# Mostrar gráfico
df.plot(...)
plt.show()
```

(_sin hipótesis, sin lectura — el plot es ruido_)

---

## 5. Estilo visual y corporativo CAPTIA.ai

| Aspecto | Estándar |
|---|---|
| **Markdown** | Numerado, jerárquico (`#`/`##`/`###`), sin emojis salvo si el usuario lo pide |
| **Mermaid** | Permitido para arquitectura / DAGs |
| **Tablas** | Para mappings, ROI, métricas comparativas |
| **Gráficas** | Título + ejes + unidades + leyenda |
| **Colores** | Paleta sobria (no abusar) |
| **Idioma** | Español en docs y narrativa; inglés en identificadores y logs |
| **Tono** | Técnico, directo, profesional. Sin "vamos a probar a ver qué pasa" |
| **Resultados** | Siempre en contexto (¿bate baseline?, ¿significativo?) |

### Anti-patrones corporativos

- **NA-E**: "Ahorra +800 €/mes" sin denominador → **citar línea de
  `economic_baseline.md`**.
- **NA-C**: "Benchmark BDG2 53M filas: 230 ms" generado sobre 100 filas
  mock → **etiquetar honestamente** o reescribir.
- "Probamos cosas" → **definir objetivo medible** antes del experimento.

---

## 6. Código (8 reglas)

| # | Regla | Detalle |
|---|---|---|
| 1 | **Imports agrupados** | 1) stdlib  2) terceros  3) `notebooks._common.*` |
| 2 | **Variables de configuración** al principio | `SEED = 42`, `DEFAULT_BUCKET`, `HORIZON_H = 24` |
| 3 | **Funciones auxiliares con type hints** | `def add_lag(df: pd.DataFrame, col: str = "value") -> pd.DataFrame:` |
| 4 | **No duplicar código** | Si una función va a usarse en 2+ notebooks → `notebooks/_common/` |
| 5 | **Celdas pequeñas** (< 50 líneas, idealmente < 30) | Una idea por celda |
| 6 | **Nombres claros** | `mae_baseline`, no `mae_b` o `m1` |
| 7 | **`display()` no `print()` masivo** | Tablas con `display(df)`, valores escalares con `print(f"...")` |
| 8 | **Controlar warnings** | `import warnings; warnings.filterwarnings("ignore", category=...)` solo si es justificado |

### Setup canónico (idéntico en los 45 notebooks)

```python
from __future__ import annotations
import os, sys
from pathlib import Path

ROOT = Path.cwd()
while ROOT.name and not (ROOT / "pyproject.toml").exists():
    ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from notebooks._common.captia_schema import (
    CANONICAL_TAGS, MEASUREMENT_TELEMETRY, MEASUREMENT_FAULT_LABELS,
    DEFAULT_BUCKET_RETENTIONS, KNOWN_VARIABLES,
    build_topic, build_line_protocol, validate_canonical_tags,
)
from notebooks._common.connection import load_env, get_influx_client, get_default_bucket
from notebooks._common.plotting import setup_default_style, plot_timeseries, plot_distribution
import notebooks._common.synthetic_mocks as mocks

SEED = 42
rng = np.random.default_rng(SEED)
setup_default_style()
load_env()
print(f"ROOT={ROOT}, SEED={SEED}, default_bucket={get_default_bucket()}")
```

> **Regla NA-G:** este setup importa todos los helpers. Aunque algunos
> no se usen en ese notebook, **el setup es invariante** — facilita
> debugging y refactoring por agentes automáticos. Si un import sobra,
> se documenta en sec 17 (errores comunes), NO se elimina del setup.

### Determinismo

- `seed=42` global.
- `np.random.default_rng(SEED)` (NO `np.random.seed()` deprecado).
- `OMP_NUM_THREADS=1` en producción para BLAS determinista.
- Mocks deterministas: `make_*` con `seed=42` por defecto.

---

## 7. Data science (10 sub-disciplinas)

### 7.1 EDA

- Descripción del dataset (shape, columnas, periodos).
- Missing values por columna y patrón temporal.
- Tipos correctos (`pd.Timestamp`, `float64`).
- Rangos físicos.
- Distribución (histograma + percentiles).
- Outliers (boxplot, IQR).
- Correlaciones (matriz de Spearman para no-linealidad).
- Comportamiento temporal (diurnal, weekly, seasonal).
- Calidad inicial (% completitud, gaps, duplicados).

### 7.2 Time series

- Frecuencia uniforme (`pd.infer_freq`).
- Gaps detectados y reportados.
- Timezone explícita (`Europe/Madrid` para Simarro).
- Resampling consciente (1min → 15min → 1h).
- Tendencia (descomposición additiva/multiplicativa).
- Estacionalidad (ADF + ACF + PACF).
- Lags relevantes (24h, 168h para weekly).
- **Sin leakage temporal** (test SIEMPRE posterior a train).
- Split temporal correcto (`TimeSeriesSplit`).
- Baseline naïve `naive_persistence_24h`.
- Métricas: MAE, RMSE, sMAPE.

### 7.3 Forecasting

- **Baseline antes de modelos avanzados** (NA-E).
- `train / validation / test` temporal estricto.
- **Nunca shuffle** en time series.
- Horizonte explicado (1h vs 6h vs 24h).
- Features documentadas (lag, rolling, calendario).
- Comparación entre modelos con IC bootstrap.
- Interpretación de errores por horizonte.
- Análisis de residuales (estacionariedad, autocorrelación).

### 7.4 Anomalías

- Separar **anomalía de dato** (sensor roto) vs **avería física**.
- Etiquetas si existen (`captia_fault_labels`).
- **No evaluar solo con accuracy** (clases desbalanceadas).
- Precision / Recall / F1 macro + matriz coste-sensible.
- Visualizar **falsos positivos** (¿son artefactos o sub-fallos?).
- Documentar umbral (¿percentil? ¿z-score? ¿learned?).
- Patrón Top-3 (Caso C·04): rule-based → IF → AE entrenado solo con normales.

### 7.5 RAG / agentes

- **Separar datos numéricos** (tools sobre InfluxDB) **de conocimiento documental** (RAG sobre `.md`).
- **No indexar series temporales completas** como texto.
- Tools tipadas con docstring: `compare_periods(variable, p1, p2) -> dict`.
- RAG para contexto normativo (EN 16798, ASHRAE, RGPD).
- Golden set de preguntas etiquetadas (`chatbot_golden_set.csv`).
- **Evaluación de alucinación** con expected_keywords.
- Trazabilidad de fuentes (chunk → documento original).

### 7.6 MLOps

- Registrar **parámetros** (`mlflow.log_params({...})`).
- Registrar **métricas** (`mlflow.log_metric(...)`).
- Registrar **artefactos** (modelo, plots, dataset hash).
- Registrar **versión de dataset** (lakeFS tag, hash determinista).
- **Reproducibilidad con seed** + `OMP_NUM_THREADS=1`.
- Comparación de experimentos en UI MLflow.
- Naming convention: `^case_[A-J]_(baseline|prod)_\d{4}$`.

### 7.7 Calidad de datos

- Reglas por **capa Medallion**:
  - **Bronce**: estructura + tipos.
  - **Plata**: schema CAPTIA + completitud + 5 tags + `value` único.
  - **Oro**: distribución (KL train vs prod) + features estables.
- **Severidad** (warning / blocking).
- **Acción recomendada** (alert Slack, block deploy, retrain trigger).
- Reportes automáticos (Flux Tasks programadas).

### 7.8 Big Data (Spark vs Pandas)

- **Justificar Spark** con números (filas, latencia, memoria).
- **Medir tiempo** con warmup (5 runs, mediana, MAD).
- **Misma operación** en pandas, polars, duckdb, Spark.
- **Comparar resultados** (¿bytes idénticos?).
- **No usar dataset pequeño** para "demostrar" Spark.
- Documentar **cuándo NO migrar** (Caso I·03: NO migrar a Spark hoy para CAPTIA).

### 7.9 Visión artificial (YOLO)

- **Separar imagen bronce** (raw JPEG, RGPD-blurred) **del conteo numérico plata** (`vehicle_count`).
- Documentar modelo (YOLOv8n, weights hash).
- Confidence threshold explícito (0.4 / 0.5 / 0.7).
- Falsos positivos / negativos visualizados.
- Versionado de imágenes (lakeFS / DVC).
- Trazabilidad imagen → conteo (timestamp, camera_id).
- Mocks deterministas: hash SHA-256 completo, **no JPEG magic bytes** (B4 fix).

### 7.10 Realismo físico

- Balance de masa CO₂ (Wang 2017): `dC/dt ∝ N(t)`.
- Leyes ASHRAE 62.1 (ventilación) y EN 16798 (IAQ index).
- Geometría solar (declinación δ, ángulo zenital θ_z).
- Histéresis en alarmas (5-min sostenido + banda rearme).
- Anti short-cycle HVAC (min on/off dwell ≥ 5 min).

---

## 8. Anti-patrones críticos (NA-A..NA-H + NA-01..NA-10)

Catálogo consolidado de las dos auditorías previas:

### Patrones transversales (NA-A..NA-H)

| ID | Patrón | Notebooks afectados | Estado |
|---|---|---|---|
| **NA-A** | Sec 19/20/21 idénticas dentro de cada caso | B, C, D, E, F, G, H, I, J | **Resuelto sec 22 (Sprint 4)**, sec 19/20/21 pendiente |
| **NA-B** | `eval_helpers.py` infrautilizado fuera de `04` | overview, A, B, parcial F | Parcial |
| **NA-C** | "Benchmark BDG2 53M" fabricada | I (todos) | Resuelto Sprint 2 (etiqueta honesta) |
| **NA-D** | Promesa-entrega rota en sec 2 | A·02, B·04, B·05, E·01, J·01 | Resuelto Sprint 3 para B·01, B·04, A·02 |
| **NA-E** | ROI sin baseline auditable | Todos | Resuelto Sprint 2 con `economic_baseline.md` |
| **NA-F** | Asserts laxos (`> 0.5`) | C·05, E·04, H·05, J·02, J·04 | Pendiente Ola-2 |
| **NA-G** | Imports masivos no usados en setup | Todos (45) | Aceptado por convención (ver §6) |
| **NA-H** | Sec 17 lista errores que el código comete | C·03, E·04, H·03 | Pendiente Ola-2 |

### Bugs específicos (NA-01..NA-10 / B1..B7)

| ID | Notebook | Bug | Estado |
|---|---|---|---|
| **B1** | `08_case_H/02_tools_influxdb` | `compare_periods` ignora `start` | Sprint 1 fix |
| **B2** | `08_case_H/04_rag_documental` | clave duplicada `expected_map` | Sprint 1 fix |
| **B3** | `08_case_H/05_evaluacion_chatbot` | claves duplicadas `route()` | Sprint 1 fix |
| **B4** | `10_case_J/02_inferencia_yolo` | JPEG magic bytes 4B | Sprint 1 fix (SHA-256) |
| **B5** | `10_case_J/01_captura_imagenes_dgt` | `fake_jpeg` rng interno | Sprint 1 fix |
| **B6** | `07_case_G/03_reglas_calidad_oro_ml` | KL `density=True` negativo | Sprint 1 fix (probabilidades) |
| **B7** | `09_case_I/03_benchmark_spark` | Spark/Dask no instalados → DataFrame vacío | Sprint 2 (recomendación honesta) |

---

## 9. Verificación automática

Cualquier notebook **debe pasar** los siguientes checks antes de ser
mergeado:

```bash
# 1. Tests de integridad (~270 checks)
uv run pytest tests/integration/test_notebooks_integrity.py -v

# 2. Lint
uv run ruff check .
uv run ruff format --check .

# 3. Ejecución determinista
uv run --group notebooks python scripts/execute_notebooks.py --workers 4 --timeout 300

# 4. Schema canónico (Bash)
bash scripts/verify_canonical_schema.sh

# 5. Mkdocs build
uv run --with mkdocs-material mkdocs build --strict

# 6. Auditoría re-generada
uv run python scripts/audit_notebooks.py --all

# 7. Score regression
uv run python scripts/audit_notebooks.py --score-delta
```

Si alguno de estos checks falla → **el PR no se mergea**.

---

## 10. Cuándo crear un notebook nuevo

| Situación | Acción |
|---|---|
| Caso de uso completamente nuevo (e.g. seguridad CCTV) | 1) Añadir caso en `docs/audit/USE_CASE_MATRIX.md`; 2) Crear `notebooks/11_case_K_*/`; 3) Crear `case_k.py` en `scripts/build_notebooks/`; 4) 5 notebooks (01..05); 5) Apéndices únicos en `_CASE_STAGE_NOTES` |
| Notebook adicional dentro de caso existente | 1) Añadir entrada en `_CASE_STAGE_NOTES`; 2) Sumar al `case_*.py`; 3) Reusar template; 4) Re-build |
| Notebook auxiliar (ejemplo aislado, demo) | NO añadir a `notebooks/` — colocar en `output/` o `tmp/jupyter-notebook/` |

---

## 11. Cuándo eliminar un notebook

| Situación | Acción |
|---|---|
| Caso obsoleto | 1) Mover a `notebooks/_archive/`; 2) Anotar en `STATUS.md` con motivo; 3) Reducir `EXPECTED_NOTEBOOK_COUNT` en tests |
| Notebook duplicado | Investigar antes de eliminar — puede que sea variante intencional |
| Notebook roto sin posibilidad de fix | Documentar en `NOTEBOOK_REFACTOR_PLAN.md` y archivar; no commit silencioso |

---

## 12. Resumen ejecutivo

**Un notebook CAPTIA profesional cumple a la vez:**

- 22 secciones canónicas (estructura validada por tests).
- Schema canónico citado y validado.
- Setup canónico bit-a-bit idéntico (determinismo).
- Helpers `_common/` reutilizados (sin reimplementar).
- Mocks etiquetados explícitamente.
- Asserts cuantitativos no triviales.
- Visualizaciones interpretadas.
- Baseline ANTES de modelo avanzado.
- ROI ancorado a `economic_baseline.md`.
- Sec 22 única vía `_CASE_STAGE_NOTES` (anti NA-A).

**Lo que NO debe hacer:**

- Hardcodear secretos / paths absolutos.
- Presentar mocks como resultados reales (NA-C).
- Modelar sin baseline (NA-E).
- Romper la promesa de la sec 2 (NA-D).
- Listar errores que el propio código comete (NA-H).
- Inventar cifras ROI sin denominador (NA-E).

---

## Referencias

- Auditoría detallada: [`../NOTEBOOK_AUDIT_DETAILED.md`](../NOTEBOOK_AUDIT_DETAILED.md)
- Auditoría inicial: [`../NOTEBOOK_AUDIT.md`](../NOTEBOOK_AUDIT.md)
- Inventario actual: [`00_NOTEBOOK_INVENTORY.md`](00_NOTEBOOK_INVENTORY.md)
- Matriz de calidad: [`NOTEBOOK_QUALITY_MATRIX.md`](NOTEBOOK_QUALITY_MATRIX.md)
- Plan de refactor: [`NOTEBOOK_REFACTOR_PLAN.md`](NOTEBOOK_REFACTOR_PLAN.md)
- Reviews por notebook: [`reviews/`](reviews/)
- Template canónico: [`CAPTIA_NOTEBOOK_TEMPLATE.md`](CAPTIA_NOTEBOOK_TEMPLATE.md)
- Spec dominio CAPTIA: [`../../specs/synthetic-bms/02-domain-spec.md`](../../specs/synthetic-bms/02-domain-spec.md)
- Baseline económico: [`../../captia/economic_baseline.md`](../../captia/economic_baseline.md)
- CENTINELA+ guía: [`../../archive/CENTINELA_Guia_Alumnos_v4.md`](../../archive/CENTINELA_Guia_Alumnos_v4.md)
- MEDALLION guía: [`../../archive/MEDALLION_Arquitectura_Guia_Referencia.md`](../../archive/MEDALLION_Arquitectura_Guia_Referencia.md)
