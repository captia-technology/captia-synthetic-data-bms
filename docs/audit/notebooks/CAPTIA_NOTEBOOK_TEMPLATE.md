# Template canónico CAPTIA — Documentación

> **Última verificación:** 2026-05-10
> **Template:** [`notebooks/_templates/CAPTIA_NOTEBOOK_TEMPLATE.ipynb`](../../../notebooks/_templates/CAPTIA_NOTEBOOK_TEMPLATE.ipynb)
> **Generador:** [`scripts/build_notebook_template.py`](../../../scripts/build_notebook_template.py)

Este template define la **estructura oficial de 22 secciones** que todo
notebook didáctico CAPTIA Synthetic Data BMS debe respetar. Es la
contraparte ejecutable de [`CAPTIA_NOTEBOOK_GUIDELINES.md`](CAPTIA_NOTEBOOK_GUIDELINES.md).

## Cuándo usarlo

- **Crear notebook nuevo** del repo (caso A..J o overview).
- **Refactorizar notebook existente** que se haya desviado de la estructura.
- **Onboarding** de un nuevo data scientist al equipo CAPTIA.
- **Material formativo** para alumnos del Curso de Especialización IA & Big Data.

## Cómo regenerarlo

```bash
uv run python -m scripts.build_notebook_template
# [template] notebooks\_templates\CAPTIA_NOTEBOOK_TEMPLATE.ipynb · 31 cells · ~23 kB
```

El template **no debe editarse a mano**. Cualquier cambio se aplica al
generador `scripts/build_notebook_template.py` para preservar
determinismo.

## Cómo clonarlo a un notebook nuevo

### Opción A — copia + sed

```powershell
# PowerShell (Windows)
Copy-Item notebooks/_templates/CAPTIA_NOTEBOOK_TEMPLATE.ipynb `
          notebooks/04_case_D_iaq_occupancy/06_nuevo_modelo.ipynb

# Luego sustituir placeholders manualmente o con un editor
```

### Opción B — generador parametrizado (futuro)

> _(Pendiente Sprint 5: extender `build_notebook_template.py` con flags
> `--case`, `--stage`, `--out` que rellenen los placeholders desde CLI.)_

## Placeholders del template

| Placeholder | Reemplazo esperado | Ejemplo |
|---|---|---|
| `{{TITLE}}` | Título legible del notebook (sec 1 H1) | `Forecast SARIMA AULA01 24h` |
| `{{CASE}}` | Etiqueta del caso `A`..`J` | `B` |
| `{{LAYER}}` | Capa Medallion textual | `bronce → plata` |
| `{{SPEC}}` | Path relativo a la spec asociada | `docs/specs/synthetic-bms/02-domain-spec.md` |
| `{{STAGE}}` | Prefijo numérico de la etapa | `04` (modelado) |
| `{{DATASET}}` | Nombre del dataset | `In-Gauge AULA01` |
| `{{ROI_VALUE_EUR_YEAR}}` | Cifra ROI auditable | `21 600` |
| `{{MOCK_FUNCTION}}` | Nombre de la función mock | `make_ingauge_aula01_mock` |
| `{{CASE_DOMAIN}}` | `domain_id` del caso | `bms_classrooms` |
| `{{VARIABLE}}` | Variable canónica | `co2_01` |
| `{{MIN}}`, `{{MAX}}` | Rangos físicos | `350`, `5000` |
| `{{SECTION}}` | Sección del baseline económico | `2.3` |
| `{{STAGE_TITLE}}` | Título de la etapa (lo rellena el builder) | `Modelado y baselines` |

## Estructura del template (22 secciones)

| # | Sección | Tipo celda | Propósito |
|---|---------|-----------|-----------|
| 0 | Cabecera trazable | md | `Caso de uso` / `Capa Medallion` / `Spec:` para tests |
| 1 | Portada corporativa | md | Metadatos legibles para humanos |
| 2 | Objetivos de aprendizaje | md | 3 objetivos medibles + scope explícito |
| 3 | Contexto del caso de uso | md | Problema de negocio + stakeholders + KPIs + ROI |
| 4 | Relación con CENTINELA+ | md | Reusabilidad sintético → real |
| 5 | Relación con arquitectura Medallion | md + Mermaid | Capa entrada / capa salida + contrato preservado |
| 6 | Datos de entrada | md (tabla) | Dataset, frecuencia, variables, periodo, tamaño |
| 7 | Setup y variables de entorno | md + py | `SETUP_BLOCK` canónico (idéntico en los 45) |
| 8 | Schema CAPTIA esperado | md + py | Constantes + `validate_canonical_tags()` |
| 9 | Carga de datos | md + py | Online InfluxDB / Offline mock |
| 10 | Validación inicial | md + py | Asserts de schema, nulos, duplicados, rangos |
| 11 | Exploración didáctica | md + py | Hipótesis ANTES del plot + descriptiva + viz |
| 12 | Transformaciones paso a paso | md + py | Funciones pequeñas con type hints |
| 13 | Visualizaciones | md | 3+ plots con interpretación |
| 14 | Modelado o análisis | md + py | Baseline → modelo intermedio → modelo final + CV temporal |
| 15 | Validación técnica | md + py | Asserts cuantitativos (modelo bate baseline; IC ≠ 0) |
| 16 | Interpretación de resultados | md | Narrativa: ¿bate baseline?, ¿dónde falla?, ¿qué pesa? |
| 17 | Errores comunes | md | ≥ 3 anti-patrones que el código evita |
| 18 | Resumen final + próximos pasos | md | Resumen 3 líneas + reutilización CENTINELA+ |
| 19 | Marco teórico (doctoral) | md (LaTeX) | Fórmulas que coincidan con secs 14-15 |
| 20 | Visión corporativa CAPTIA | md (tabla ROI) | Propuesta valor + ROI ancorado a baseline + riesgos |
| 21 | Bibliografía y referencias | md | ≥ 4 referencias APA-lite con DOI/URL |
| 22 | Etapa del pipeline (única) | md | Generada por `_CASE_STAGE_NOTES` (45 únicas) |

## Reglas de oro al rellenar el template

1. **No alterar la cabecera trazable** (`Caso de uso` / `Capa Medallion` /
   `Spec:`) — los tests integridad la requieren textualmente.
2. **No tocar `SETUP_BLOCK`** — debe ser bit-a-bit idéntico al de los 45
   notebooks. Es la fuente de reproducibilidad determinista.
3. **Todos los `# MOCK`** se etiquetan explícitamente (`# MOCK — sintético`).
4. **Section 22 la rellena el builder** automáticamente desde
   `_CASE_STAGE_NOTES` — no escribir manualmente; añadir entrada al dict
   si el (caso × etapa) es nuevo.
5. **Cada cifra ROI de sec 20** debe citar la sección concreta de
   `docs/captia/economic_baseline.md`.
6. **La fórmula de sec 19** debe coincidir con la implementación de las
   secs 14-15 (cohesión LaTeX↔código, anti-patrón NA-D).
7. **Cada plot** lleva título, ejes, unidades, leyenda e interpretación.
8. **Cada modelo lleva baseline** (NA-E: "no modelo sin baseline").
9. **CV temporal** con `TimeSeriesSplit` — nunca `train_test_split(shuffle=True)`
   en time series.
10. **Asserts cuantitativos** (no `> 0.5` trivial, sino `> baseline_metric`).

## Validación del template

```bash
# Cuenta correcta de notebooks (45, NO 46)
uv run python -c "import pathlib; print(len([p for p in pathlib.Path('notebooks').rglob('*.ipynb') if '_templates' not in p.parts]))"
# 45

# Tests integridad (template excluido)
uv run pytest tests/integration/test_notebooks_integrity.py -q
# 183 passed

# Inventory regenerado (template no aparece)
uv run python scripts/audit_notebooks.py --inventory
# [inventory] docs\audit\notebooks\00_NOTEBOOK_INVENTORY.md (...)
```

## Historia del template

- **2026-05-10** — creación inicial (Sprint 5 / auditoría profesional).
  31 cells, 22 secciones, idempotente vía `build_notebook_template.py`.
- _(Próximas modificaciones se registran aquí con commit hash)_.

## Referencias

- Estructura completa con anti-patrones: [`CAPTIA_NOTEBOOK_GUIDELINES.md`](CAPTIA_NOTEBOOK_GUIDELINES.md)
- Helpers reutilizables: [`../../../notebooks/_common/`](../../../notebooks/_common/)
- Builder de los 45 notebooks: [`../../../scripts/build_notebooks/`](../../../scripts/build_notebooks/)
- Schema canónico CAPTIA: [`../../specs/synthetic-bms/02-domain-spec.md`](../../specs/synthetic-bms/02-domain-spec.md)
- Baseline económico: [`../../captia/economic_baseline.md`](../../captia/economic_baseline.md)
