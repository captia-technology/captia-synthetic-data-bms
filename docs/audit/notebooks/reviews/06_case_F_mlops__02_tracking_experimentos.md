# Review — `notebooks/06_case_F_mlops/02_tracking_experimentos.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** MLOps  
> **Etapa:** 02 (Bronce → Plata (ETL))  
> **Capa Medallion declarada:** transversal  
> **Spec:** `docs/specs/synthetic-bms/01-product-spec.md`  
> **Score:** **8.1 / 10** · Veredicto **B** · Prioridad **P2**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/06_case_F_mlops/02_tracking_experimentos.ipynb` |
| Título | Caso F · 02 Tracking de experimentos con MLflow local |
| Celdas md / code | 23 / 6 |
| Secciones distintas | 22 |
| Outputs persistidos | 6 / 6 (100.0%) |
| Helpers `_common` | `captia_schema`, `connection`, `eval_helpers`, `plotting`, `synthetic_mocks` |
| Cita schema CAPTIA | sí |
| `assert` presente | sí |
| Mocks etiquetados | — |
| Sin secretos inline | sí |
| Sin paths absolutos | sí |
| Datasets detectados | BDG2 educational (público resampled) |

## 1. Resumen ejecutivo

<!-- AUTO -->
Notebook **02_tracking_experimentos** del caso **MLOps**, etapa **02** (capa Bronce → Plata (ETL)). Score **8.1/10**, veredicto **B**. 6/6 celdas de código con outputs persistidos (100.0%). Sin bugs P0/P1 reportados. Helpers `_common` reutilizados: `captia_schema`, `connection`, `eval_helpers`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Caso F · 02 Tracking de experimentos con MLflow local**.  
Tracking experimentos baseline vs improved con mlflow.set_tag('lakefs_tag', ...).

## 3. Caso de uso asociado

- **Dominio:** MLOps.
- **Caso CAPTIA Synthetic Data BMS:** `06_case_F_mlops`.
- **Spec asociado:** `docs/specs/synthetic-bms/01-product-spec.md`.
- **Capa Medallion:** transversal.

## 4. Nivel didáctico esperado

**Nivel:** I ({B=básico, I=intermedio, A=avanzado}).

<!-- TODO: justificar nivel con prerequisitos del notebook -->

## 5. Qué funciona bien

- Estructura de **22 secciones** (target 22).
- Cita explícita del schema canónico CAPTIA.
- Helpers `_common` reutilizados (`captia_schema`, `connection`, `eval_helpers`, `plotting`, `synthetic_mocks`).
- Outputs persistidos celda a celda (100.0%).
- `assert`-driven validación.

**Curado:** Tag lakeFS para auditoría EU AI Act. Naming convention aplicada.

## 6. Problemas técnicos

- _Sin bugs P0/P1 conocidos._

**Curado:** Anteriormente `mlflow disponible: False` (P0-3); Sprint 1 añadió `mlflow>=2.18` al group. Verificar que ejecuta con tracking_uri sqlite.

## 7. Problemas didácticos

**Curado:** Falta visualizar la UI MLflow (screenshot o instrucciones).

## 8. Problemas de reproducibilidad

- verificar manualmente.
- Sin paths absolutos.
- Sin secretos inline.

<!-- TODO: validar `INFLUX_OFFLINE` fallback funciona; idempotencia del setup; determinismo. -->

## 9. Problemas de estilo corporativo CAPTIA.ai

<!-- TODO: comprobar tono, terminología, links a economic_baseline, alineación CENTINELA+. -->

## 10. Problemas de arquitectura Medallion

- **Capa declarada:** transversal.
- **Etapa:** 02 (Bronce → Plata (ETL)).

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

**B** — _Bueno, requiere mejora_.

## Scorecard detallado (auditoría deep-9 / Sprints)

Pedag 6 · Código 6 · Rigor 6 · Visu 6 · Ejer 6 · ErrCom 7 · ROI 6 · Reuso 7 · Coher 7 → **6.6**

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
