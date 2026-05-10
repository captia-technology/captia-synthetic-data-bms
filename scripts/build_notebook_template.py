"""Genera el template canónico CAPTIA de notebooks didácticos.

Salida: ``notebooks/_templates/CAPTIA_NOTEBOOK_TEMPLATE.ipynb`` con la
**estructura oficial de 22 secciones** (1-18 base + 19 marco teórico + 20
visión corporativa + 21 bibliografía + 22 nota etapa única). El template
contiene **placeholders** (``{{TITLE}}``, ``{{CASE}}``, ``{{LAYER}}``,
``{{SPEC}}``, etc.) y prompts pedagógicos en cada sección — sin lógica
caso-específica.

Uso::

    uv run python scripts/build_notebook_template.py

Para clonar el template a un notebook nuevo::

    cp notebooks/_templates/CAPTIA_NOTEBOOK_TEMPLATE.ipynb \
       notebooks/04_case_D_iaq_occupancy/06_nuevo_modelo.ipynb
    # luego sustituir {{...}} placeholders.

Diseño:

- Reusa ``scripts._nb_builder.write_notebook`` para producir nbformat 4
  con cell IDs deterministas (SHA-256).
- Reusa ``scripts.build_notebooks._helpers.header`` para la cabecera
  trazable (Caso de uso / Capa Medallion / Spec).
- Reusa ``scripts._nb_builder.SETUP_BLOCK`` para que el setup canónico sea
  bit-a-bit idéntico al de los 45 notebooks didácticos.

El template se excluye del rglob de
``tests/integration/test_notebooks_integrity.py`` porque el path
``notebooks/_templates/`` está fuera del walk; ver el filtro en ese test.
"""

from __future__ import annotations

from pathlib import Path

from scripts._nb_builder import SETUP_BLOCK, header, write_notebook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "_templates" / "CAPTIA_NOTEBOOK_TEMPLATE.ipynb"

# Placeholders en formato `{{NAME}}` para `sed`/`envsubst` o reemplazo manual.
PLACEHOLDERS = {
    "TITLE": "{{TITLE}}",
    "CASE": "{{CASE}}",
    "LAYER": "{{LAYER}}",
    "SPEC": "{{SPEC}}",
    "STAGE": "{{STAGE}}",
    "DATASET": "{{DATASET}}",
    "ROI_VALUE": "{{ROI_VALUE_EUR_YEAR}}",
}


def _md_section(n: int, name: str, body: str) -> tuple[str, str]:
    return ("md", f"## {n}. {name}\n\n{body.rstrip()}\n")


def _md(text: str) -> tuple[str, str]:
    return ("md", text)


def _py(code: str) -> tuple[str, str]:
    return ("py", code)


def build_template_cells() -> list[tuple[str, str]]:
    cells: list[tuple[str, str]] = []

    # 0. Cabecera (placeholder).
    cells.append(
        _md(
            header(
                kind="Tutorial",
                title=PLACEHOLDERS["TITLE"],
                case=PLACEHOLDERS["CASE"],
                layer=PLACEHOLDERS["LAYER"],
                spec=PLACEHOLDERS["SPEC"],
            )
        )
    )

    # 1. Portada extendida (metadata corporativa).
    cells.append(
        _md_section(
            1,
            "Portada corporativa",
            f"""
**Proyecto:** CAPTIA Synthetic Data BMS
**Caso de uso:** {PLACEHOLDERS["CASE"]}
**Capa Medallion:** {PLACEHOLDERS["LAYER"]}
**Etapa pipeline:** {PLACEHOLDERS["STAGE"]} (01-EDA, 02-ETL, 03-Features, 04-Modelado, 05-Validación)
**Spec asociada:** `{PLACEHOLDERS["SPEC"]}`
**Última revisión:** 2026-05-10
**Estado:** Validado / Experimental / Requiere datos reales
**Audiencia:** Alumnos del Curso de Especialización IA & Big Data 2025-2026 (IES Dr. Lluís Simarro), CAPTIA Technology, integradores de CENTINELA+.

> Material docente reutilizable. Cuando llegue `simarro-prod` con datos
> reales, este notebook se ejecuta sobre `INFLUX_OFFLINE=false` sin
> reescribir lógica.
""",
        )
    )

    # 2. Objetivos de aprendizaje.
    cells.append(
        _md_section(
            2,
            "Objetivos de aprendizaje",
            """
Al terminar este notebook el alumno será capaz de:

1. _(objetivo medible 1 — verbo de Bloom: identificar, calcular, validar, comparar...)_
2. _(objetivo medible 2)_
3. _(objetivo medible 3)_

**Lo que NO cubre este notebook:** _(delimitar alcance para evitar saltos didácticos)_.
""",
        )
    )

    # 3. Contexto del caso de uso.
    cells.append(
        _md_section(
            3,
            "Contexto del caso de uso",
            f"""
Resumen del caso **{PLACEHOLDERS["CASE"]}** desde la perspectiva CAPTIA:

- **Problema de negocio:** _(qué dolor del cliente resuelve)_.
- **Stakeholders:** _(director del IES Simarro, profesorado, equipo técnico CAPTIA, futuros centros CENTINELA+)_.
- **KPIs esperados:** _(MAE / F1 / Recall@k / latencia / disponibilidad)_.
- **Impacto económico:** _(referencia a `docs/captia/economic_baseline.md`, sección concreta)_.

> Una buena sec 3 motiva al alumno antes de mostrarle código. Si no
> entiende el problema, el código es ruido.
""",
        )
    )

    # 4. Relación con CENTINELA+.
    cells.append(
        _md_section(
            4,
            "Relación con CENTINELA+",
            f"""
Este notebook pivota sobre el sistema real **CENTINELA+** (CAPTIA Technology):

- **Sistema fuente:** {PLACEHOLDERS["DATASET"]} (sintético hoy / real cuando llegue `simarro-prod`).
- **Reutilización:** ¿qué cambia entre datos sintéticos y reales? Ideal: solo `INFLUX_OFFLINE=false` y `domain_id`.
- **Convenciones operativas:** topics MQTT `captia/{{env}}/{{tenant}}/{{site}}/{{device}}/telemetry/{{name}}`.

> Cuando un alumno lleva este notebook al puesto de trabajo en CENTINELA+,
> debe ser una transición sin sobresaltos.
""",
        )
    )

    # 5. Relación con arquitectura Medallion.
    cells.append(
        _md_section(
            5,
            "Relación con arquitectura Medallion",
            f"""
Este notebook trabaja en la capa **{PLACEHOLDERS["LAYER"]}** del esquema Medallion CAPTIA:

```mermaid
flowchart LR
    A[Bronze<br/>raw CSV/JSON] --> B[Silver<br/>captia_point + 5 tags]
    B --> C[Gold<br/>features + modelos]
    C --> D[Servir<br/>API / Grafana / Chatbot]
```

- **Entrada:** _(qué capa lee este notebook)_.
- **Salida:** _(qué capa produce, dónde escribe)_.
- **Contrato preservado:** schema canónico `captia_point` + 5 tags + field `value` no se altera.

> Ver guía completa en `docs/archive/MEDALLION_Arquitectura_Guia_Referencia.md`.
""",
        )
    )

    # 6. Datos de entrada.
    cells.append(
        _md_section(
            6,
            "Datos de entrada",
            f"""
| Atributo | Valor |
|---|---|
| Dataset | {PLACEHOLDERS["DATASET"]} |
| Tipo | sintético / público mockeado / real |
| Frecuencia | _(1 min / 15 min / 1 h)_ |
| Variables | _(temperature_01, co2_01, power_kw, ...)_ |
| Periodo | _(7 d / 30 d / 12 m)_ |
| Tamaño esperado | _(filas, MB)_ |

**Origen real cuando llegue `simarro-prod`:** _(InfluxDB bucket `telemetry` con tag `domain_id={{...}}`)_.

> Los datos sintéticos son **etiquetados** (`# MOCK — sintético`). Nunca
> presentar mocks como resultados reales.
""",
        )
    )

    # 7. Setup canónico.
    cells.append(
        _md_section(
            7,
            "Setup y variables de entorno",
            """
Cargamos las variables de entorno (`.env`), inicializamos `numpy` con
`seed=42` y aplicamos el estilo de plotting compartido. Los helpers viven
en `notebooks/_common/`.

> Este bloque es **idéntico en los 45 notebooks** del repo. Cualquier
> cambio aquí afecta a todo el material — coordinar con el equipo CAPTIA
> antes de modificar.
""",
        )
    )
    cells.append(_py(SETUP_BLOCK))

    # 8. Schema CAPTIA esperado.
    cells.append(
        _md_section(
            8,
            "Schema CAPTIA esperado",
            """
El contrato canónico CAPTIA es **inmutable**:

- **Measurement:** `captia_point` (telemetría continua); `captia_fault_labels` (eventos discretos opcionales).
- **Tags (5):** `captia_env`, `domain_id`, `site_id`, `asset_id`, `variable`.
- **Field:** `value` (float; estados booleanos como `1.0`/`0.0`).
- **Topic MQTT:** `captia/{env}/{tenant}/{site}/{device}/telemetry/{name}`.

> No alterar nombres de tags ni measurement. Cualquier ETL que llegue
> aquí debe pasar por `validate_canonical_tags()`.
""",
        )
    )
    cells.append(
        _py(
            """\
# Validación rápida del schema esperado
print("Measurement:", MEASUREMENT_TELEMETRY)
print("Tags canónicos:", CANONICAL_TAGS)
# Reemplazar los placeholders por valores reales del notebook concreto:
sample_tags = {
    "captia_env": "dev",
    "domain_id": "PLACEHOLDER_CASE_DOMAIN",   # ej. bms_classrooms
    "site_id": "ies_simarro",
    "asset_id": "AULA01",
    "variable": "PLACEHOLDER_VARIABLE",       # ej. co2_01
}
validate_canonical_tags(sample_tags)
print("Schema canónico validado")
"""
        )
    )

    # 9. Carga de datos.
    cells.append(
        _md_section(
            9,
            "Carga de datos",
            """
Cargamos el dataset desde:

- **Online (con stack):** InfluxDB `bucket=telemetry` filtrado por `domain_id` y `variable`.
- **Offline (sin stack):** mock determinista en `notebooks/_data/{{DATASET}}_mock.csv` (`# MOCK — sintético`).

El fallback offline garantiza que el notebook se ejecuta sin dependencias
externas en clase. `INFLUX_OFFLINE=true` activa el modo offline.
""",
        )
    )
    cells.append(
        _py(
            """\
# MOCK — sintético (placeholder)
df = mocks.{{MOCK_FUNCTION}}()
print(f"Filas={len(df)}, columnas={list(df.columns)}")
display(df.head())
"""
        )
    )

    # 10. Validación inicial.
    cells.append(
        _md_section(
            10,
            "Validación inicial de datos",
            """
Antes de cualquier transformación, verificamos:

1. **Existencia y no vacío** del DataFrame.
2. **Schema** (columnas esperadas, tipos).
3. **Timestamps** monotónicos crecientes (`is_monotonic_increasing`).
4. **Nulos por columna** (% y patrón temporal).
5. **Duplicados** por (`asset_id`, `variable`, timestamp).
6. **Rangos físicos** (`temperature ∈ [10, 40]`, `co2 ∈ [350, 5000]`...).

> Validar **antes** de visualizar evita interpretar artefactos como
> patrones reales.
""",
        )
    )
    cells.append(
        _py(
            """\
# Validaciones mínimas (asserts)
assert len(df) > 0, "DataFrame vacío"
assert "value" in df.columns, "Falta columna `value`"
# assert df.index.is_monotonic_increasing, "Timestamps no monotónicos"
# assert df["value"].between({{MIN}}, {{MAX}}).all(), "Valores fuera de rango físico"
nulls_pct = df.isna().mean() * 100
print(f"Nulos por columna (%): {nulls_pct.to_dict()}")
"""
        )
    )

    # 11. Exploración didáctica.
    cells.append(
        _md_section(
            11,
            "Exploración didáctica",
            """
**Hipótesis a explorar antes de plotear:** _(qué patrón esperamos ver y por qué)_.

Estadística descriptiva + visualizaciones progresivas:

1. Distribución global de `value`.
2. Comportamiento temporal (tendencia, estacionalidad).
3. Correlaciones con variables co-ocurrentes.

> No mostrar gráficos sin **interpretación** debajo.
""",
        )
    )
    cells.append(
        _py(
            """\
# Estadística básica
display(df.describe())
# Visualización 1: distribución
fig, ax = plt.subplots(figsize=(8, 3))
df["value"].hist(bins=40, ax=ax)
ax.set_title("Distribución de value (placeholder)")
ax.set_xlabel("value")
ax.set_ylabel("frecuencia")
plt.show()
"""
        )
    )

    # 12. Transformaciones.
    cells.append(
        _md_section(
            12,
            "Transformaciones paso a paso",
            """
Cada transformación se aplica como **función pequeña** con type hints:

```python
def add_lag_24h(df: pd.DataFrame, col: str = "value") -> pd.DataFrame:
    \"\"\"Añade columna ``lag_24h`` shifteada 24 h hacia atrás.\"\"\"
    out = df.copy()
    out[f"{col}_lag_24h"] = out[col].shift(periods=24, freq="1h")
    return out
```

> No mutar el DataFrame original. Usar `.copy()` y nombres explícitos.
""",
        )
    )
    cells.append(_py("# Aplicar transformaciones aquí\n# df_t = transform_step_1(df)\n"))

    # 13. Visualizaciones.
    cells.append(
        _md_section(
            13,
            "Visualizaciones",
            """
Visualizaciones con **título, ejes, unidades** y leyenda. Mínimo 3 plots
con interpretación textual debajo.

> Considera usar los plots diagnostic 4-panel:
>
> - `plot_regression_diagnostic(y_true, y_pred, ...)` — modelos regresión.
> - `plot_classification_diagnostic(y_true, y_score, ...)` — modelos clasificación.
> - `plot_iot_pipeline_diagnostic(...)` — series temporales IoT.
""",
        )
    )

    # 14. Modelado / análisis.
    cells.append(
        _md_section(
            14,
            "Modelado o análisis",
            """
**Antes de modelar:** un baseline simple. _Sin baseline, ningún modelo es defendible._

| Modelo | Tipo | Por qué se incluye |
|---|---|---|
| Baseline naïve / climatología / regla física | trivial | Punto de comparación |
| Modelo intermedio (RF / XGBoost) | tabular | Feature engineering al máximo |
| Modelo final (SARIMA / LSTM / IsolationForest) | dominio | Solo si supera al intermedio |

**Cross-validation temporal** (`TimeSeriesSplit`) — nunca shuffle en time series.

**Métricas:**
- Regresión: MAE, RMSE, sMAPE + IC bootstrap 95 %.
- Clasificación: Precision, Recall, F1 macro + matriz de confusión + balanced_accuracy.
""",
        )
    )
    cells.append(
        _py(
            """\
# Baseline + modelo (placeholder)
# from notebooks._common.eval_helpers import (
#     bootstrap_ci, naive_persistence_24h, time_series_cv_evaluate
# )
# baseline_pred = naive_persistence_24h(y_train, horizon=len(y_test))
# mae_baseline, ci_low, ci_high = bootstrap_ci(y_test, baseline_pred, metric="mae")
# print(f"Baseline MAE = {mae_baseline:.3f} [{ci_low:.3f}, {ci_high:.3f}]")
"""
        )
    )

    # 15. Validación técnica.
    cells.append(
        _md_section(
            15,
            "Validación técnica",
            """
**Asserts no triviales** que cuantifican la calidad del resultado:

```python
assert mae_model < mae_baseline, (
    f"El modelo NO bate al baseline (model={mae_model:.3f} vs baseline={mae_baseline:.3f})"
)
assert ci_low > 0, "IC bootstrap atraviesa cero — modelo no significativo"
```

**Sin asserts, no hay validación.** Un notebook con métricas pero sin
asserts pasa pruebas vacías.
""",
        )
    )
    cells.append(
        _py(
            """\
# Asserts cuantitativos (placeholder)
# assert mae_model < mae_baseline, "Modelo no bate al baseline"
# assert f1_score >= 0.7, "F1 < 0.7 — modelo no listo para producción"
"""
        )
    )

    # 16. Interpretación.
    cells.append(
        _md_section(
            16,
            "Interpretación de resultados",
            """
**¿Qué muestra el resultado?** Texto narrativo (5-10 líneas) interpretando:

1. ¿Bate al baseline? ¿Por cuánto? ¿Es significativo (IC no atraviesa 0)?
2. ¿Dónde falla el modelo? (residuales, outliers, regímenes)
3. ¿Qué features pesan más? (feature importance, SHAP)
4. ¿Cuál es el coste de un FN / FP en el contexto operativo?

> Métricas sin interpretación = informe vacío. _El alumno aprende a
> defender un resultado_, no a hacer click.
""",
        )
    )

    # 17. Errores comunes.
    cells.append(
        _md_section(
            17,
            "Errores comunes (anti-patrones)",
            """
Lista priorizada (≥ 3 entradas) de errores **que el código de arriba evita**:

1. **Leakage temporal** — usar `shuffle=True` en `train_test_split` con time series.
2. **Baseline ausente** — entrenar XGBoost sin compararlo con `naive_persistence_24h`.
3. **Asserts ad-hoc** — comprobar `metric > 0.5` en lugar de `metric > baseline_metric`.
4. _(añadir más errores específicos del dominio: HVAC, RAG, Spark, YOLO, etc.)_

> Si el notebook lista un error que el propio código comete (NA-H), corregirlo.
""",
        )
    )

    # 18. Resumen y próximos pasos.
    cells.append(
        _md_section(
            18,
            "Resumen final y próximos pasos",
            f"""
**Qué hemos hecho:**

- _(resumen 3 líneas)_

**Próximo notebook:** `_(siguiente notebook del caso)_`.
**Documento web del caso:** `docs/use-cases/{PLACEHOLDERS["CASE"]}.md`.

**Reutilización con CENTINELA+:**

1. Levantar stack: `make demo` o `task up`.
2. `INFLUX_OFFLINE=false` en `.env`.
3. Re-ejecutar notebook → mismas funciones, datos reales.
4. Validar schema canónico con `scripts/verify_canonical_schema.sh`.
""",
        )
    )

    # 19. Marco teórico.
    cells.append(
        _md_section(
            19,
            "Marco teórico (nivel doctoral)",
            r"""
Fundamentos matemáticos que sostienen el modelo / análisis. Renderizado
con MathJax (Jupyter) y `pymdownx.arithmatex` (MkDocs).

**Ejemplo (clasificación binaria con desbalance):**

$$
\mathrm{F}_1 = \frac{2 \cdot \mathrm{Precision} \cdot \mathrm{Recall}}{\mathrm{Precision} + \mathrm{Recall}}
$$

**Intervalo de confianza bootstrap (Efron 1979):**

$$
\widehat{\theta} \pm 1.96 \cdot \widehat{\sigma}_{\mathrm{boot}}, \quad
\widehat{\sigma}_{\mathrm{boot}}^2 = \frac{1}{B-1} \sum_{b=1}^{B}
(\widehat{\theta}^*_b - \overline{\widehat{\theta}^*})^2
$$

**Anclar la teoría al código:** la fórmula citada aquí debe **coincidir
con la implementación** de las secciones 14-15 (NA-D / cohesión LaTeX↔código).
""",
        )
    )

    # 20. Visión corporativa.
    cells.append(
        _md_section(
            20,
            "Visión corporativa CAPTIA",
            f"""
### Propuesta de valor

_(2-3 líneas anclando el notebook al producto CAPTIA y al portafolio CENTINELA+)._

### ROI estimado

| Concepto | Valor anual | Fuente |
|---|---|---|
| _(automatización L1, ahorro compute, reducción incidencias)_ | {PLACEHOLDERS["ROI_VALUE"]} €/año | `docs/captia/economic_baseline.md` §{{SECTION}} |

### Riesgos y mitigaciones

- **Riesgo 1:** _(qué falla si llega `simarro-prod` con datos reales)_.
  - **Mitigación:** _(cómo se cubre — alerts, fallback, validación)_.
- **Riesgo 2 (compliance):** EU AI Act / RGPD si aplica.

> Cualquier cifra ROI debe ser **derivable** de
> [`docs/captia/economic_baseline.md`](../../docs/captia/economic_baseline.md).
> No inventar denominadores.
""",
        )
    )

    # 21. Bibliografía.
    cells.append(
        _md_section(
            21,
            "Bibliografía y referencias",
            """
Formato APA-lite con DOI/URL cuando exista:

- Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). _Isolation Forest_. ICDM. doi:10.1109/ICDM.2008.17
- Hinton, G. E., & Salakhutdinov, R. R. (2006). _Reducing the dimensionality of data with neural networks_. Science 313(5786), 504-507.
- ASHRAE Standard 62.1 (2022). _Ventilation for Acceptable Indoor Air Quality_.
- EN 16798-1:2019. _Energy performance of buildings — Ventilation for buildings_.
- Documentación CAPTIA: `docs/specs/synthetic-bms/02-domain-spec.md`.

> Mínimo 4 referencias reales (no autoreferenciales).
""",
        )
    )

    # 22. Etapa del pipeline (placeholder; el builder rellena con _CASE_STAGE_NOTES).
    cells.append(
        _md_section(
            22,
            "Etapa del pipeline · {{STAGE_TITLE}}",
            f"""
_(El builder de los 45 notebooks rellena automáticamente esta sección
con una nota etapa-única por (caso × etapa) tomada de
`scripts/build_notebooks/_helpers.py:_CASE_STAGE_NOTES`. Mantener este
placeholder en el template hace explícito que la sección 22 es
**siempre única** — atajo para evitar el patrón NA-A.)_

**Stage:** {PLACEHOLDERS["STAGE"]} · **Caso:** {PLACEHOLDERS["CASE"]}.

> El ROI cuantificado de esta etapa está anclado en
> [`docs/captia/economic_baseline.md`](../../docs/captia/economic_baseline.md) —
> cualquier cifra de la sección 20 es derivable de ahí, no inventada.
""",
        )
    )

    return cells


def write_template() -> Path:
    cells = build_template_cells()
    write_notebook(
        path=OUT,
        title=PLACEHOLDERS["TITLE"],
        cells=cells,
    )
    return OUT


def main() -> None:
    out = write_template()
    size = out.stat().st_size
    n_cells = len(build_template_cells())
    print(f"[template] {out.relative_to(ROOT)} · {n_cells} cells · {size:,} bytes")


if __name__ == "__main__":
    main()
