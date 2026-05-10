# Review — `notebooks/09_case_I_spark_vs_pandas/03_benchmark_spark.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** Big Data  
> **Etapa:** 03 (Plata → Oro (Features))  
> **Capa Medallion declarada:** bronce → plata  
> **Spec:** `docs/specs/synthetic-bms/01-product-spec.md`  
> **Score:** **7.8 / 10** · Veredicto **C** · Prioridad **P2**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/09_case_I_spark_vs_pandas/03_benchmark_spark.ipynb` |
| Título | Caso I · 03 Benchmark con Spark (o Dask como fallback) |
| Celdas md / code | 23 / 7 |
| Secciones distintas | 22 |
| Outputs persistidos | 7 / 7 (100.0%) |
| Helpers `_common` | `captia_schema`, `connection`, `plotting`, `synthetic_mocks` |
| Cita schema CAPTIA | sí |
| `assert` presente | sí |
| Mocks etiquetados | — |
| Sin secretos inline | sí |
| Sin paths absolutos | sí |
| Datasets detectados | BDG2 educational (público resampled) |

## 1. Resumen ejecutivo

<!-- AUTO -->
Notebook **03_benchmark_spark** del caso **Big Data**, etapa **03** (capa Plata → Oro (Features)). Score **7.8/10**, veredicto **C**. 7/7 celdas de código con outputs persistidos (100.0%). Bugs P0/P1 documentados (ver §6). Helpers `_common` reutilizados: `captia_schema`, `connection`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Caso I · 03 Benchmark con Spark (o Dask como fallback)**.  
Bottom-1 (3.5/10) → reescrito como recomendación honesta CAPTIA: NO migrar a Spark hoy.

## 3. Caso de uso asociado

- **Dominio:** Big Data.
- **Caso CAPTIA Synthetic Data BMS:** `09_case_I_spark_vs_pandas`.
- **Spec asociado:** `docs/specs/synthetic-bms/01-product-spec.md`.
- **Capa Medallion:** bronce → plata.

## 4. Nivel didáctico esperado

**Nivel:** A ({B=básico, I=intermedio, A=avanzado}).

<!-- TODO: justificar nivel con prerequisitos del notebook -->

## 5. Qué funciona bien

- Estructura de **22 secciones** (target 22).
- Cita explícita del schema canónico CAPTIA.
- Helpers `_common` reutilizados (`captia_schema`, `connection`, `plotting`, `synthetic_mocks`).
- Outputs persistidos celda a celda (100.0%).
- `assert`-driven validación.

**Curado:** Sprint 2 reescritura: tabla 4 escenarios (5M / 38M / 53M / 500M filas) con motor recomendado (pandas / polars / duckdb / Spark).

## 6. Problemas técnicos

- B7: `pyspark` y `dask` no instalados → DataFrame vacío entregado como artefacto (Alta)

**Curado:** (resuelto Sprint 2) — B7 original: `pyspark` y `dask` no instalados → DataFrame vacío entregado como artefacto.

## 7. Problemas didácticos

**Curado:** Decisión defensiva CAPTIA: Spark NO se justifica por performance hoy. Migración solo cuando se supere 500M filas/dataset (~2030 a ritmo actual).

## 8. Problemas de reproducibilidad

- verificar manualmente.
- Sin paths absolutos.
- Sin secretos inline.

<!-- TODO: validar `INFLUX_OFFLINE` fallback funciona; idempotencia del setup; determinismo. -->

## 9. Problemas de estilo corporativo CAPTIA.ai

<!-- TODO: comprobar tono, terminología, links a economic_baseline, alineación CENTINELA+. -->

## 10. Problemas de arquitectura Medallion

- **Capa declarada:** bronce → plata.
- **Etapa:** 03 (Plata → Oro (Features)).

<!-- TODO: ¿lee bronce sin mutar? ¿escribe plata respetando schema? ¿genera oro reutilizable? -->

## 11. Problemas de schema CAPTIA / CENTINELA+

- **Cita schema:** sí
- **Helpers schema utilizados:** sí

<!-- TODO: validar que tags son exactamente los 5 canónicos; measurement único `captia_point`. -->

## 12. Riesgos para alumnos

<!-- TODO: identificar conceptos confusos, terminología cambiante, saltos didácticos. -->

## 13. Riesgos para uso profesional

<!-- TODO: ¿es defendible ante un auditor externo? ¿el ROI es trazable? ¿hay leakage? -->

## 14. Cambios recomendados

<!-- TODO: lista priorizada con líneas concretas o helpers a invocar -->

1. _(añadir cambio 1)_
2. _(añadir cambio 2)_
3. _(añadir cambio 3)_

## 15. Prioridad

**P2** — pulido.

## 16. Veredicto

**C** — _Útil pero necesita refactor serio_.

## Scorecard detallado (auditoría deep-9 / Sprints)

Pedag 5 · Código 4 · Rigor 4 · Visu 3 · Ejer 4 · ErrCom 5 · ROI 4 · Reuso 4 · Coher 4 → **3.5** (pre-Sprint 2)

## Datasets utilizados

- BDG2 educational (público resampled)

## Patrones NA-* aplicables

<!-- TODO: marcar cuáles de NA-A..NA-H + NA-01..NA-10 aplican a este notebook concreto -->

## Referencias

- Auditoría detallada: [`../../NOTEBOOK_AUDIT_DETAILED.md`](../../NOTEBOOK_AUDIT_DETAILED.md)
- Auditoría inicial deep-9: [`../../NOTEBOOK_AUDIT.md`](../../NOTEBOOK_AUDIT.md)
- Baseline económico: [`../../../captia/economic_baseline.md`](../../../captia/economic_baseline.md)
- Plan de uso: [`../../NOTEBOOK_PLAN.md`](../../NOTEBOOK_PLAN.md)
- Matriz casos de uso: [`../../USE_CASE_MATRIX.md`](../../USE_CASE_MATRIX.md)
