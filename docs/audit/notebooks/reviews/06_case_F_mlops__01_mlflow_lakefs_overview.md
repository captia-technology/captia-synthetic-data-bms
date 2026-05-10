# Review — `notebooks/06_case_F_mlops/01_mlflow_lakefs_overview.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** MLOps  
> **Etapa:** 01 (Bronce → Plata (EDA))  
> **Capa Medallion declarada:** transversal  
> **Spec:** `docs/specs/synthetic-bms/01-product-spec.md`  
> **Score:** **7.7 / 10** · Veredicto **C** · Prioridad **P2**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/06_case_F_mlops/01_mlflow_lakefs_overview.ipynb` |
| Título | Caso F · 01 MLflow + lakeFS — visión general |
| Celdas md / code | 23 / 7 |
| Secciones distintas | 22 |
| Outputs persistidos | 7 / 7 (100.0%) |
| Helpers `_common` | `captia_schema`, `connection`, `plotting`, `synthetic_mocks` |
| Cita schema CAPTIA | sí |
| `assert` presente | sí |
| Mocks etiquetados | — |
| Sin secretos inline | sí |
| Sin paths absolutos | sí |
| Datasets detectados | — |

## 1. Resumen ejecutivo

<!-- AUTO -->
Notebook **01_mlflow_lakefs_overview** del caso **MLOps**, etapa **01** (capa Bronce → Plata (EDA)). Score **7.7/10**, veredicto **C**. 7/7 celdas de código con outputs persistidos (100.0%). Sin bugs P0/P1 reportados. Helpers `_common` reutilizados: `captia_schema`, `connection`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Caso F · 01 MLflow + lakeFS — visión general**.  
Hello-world MLflow + naming convention CAPTIA + lakeFS tagging.

## 3. Caso de uso asociado

- **Dominio:** MLOps.
- **Caso CAPTIA Synthetic Data BMS:** `06_case_F_mlops`.
- **Spec asociado:** `docs/specs/synthetic-bms/01-product-spec.md`.
- **Capa Medallion:** transversal.

## 4. Nivel didáctico esperado

**Nivel:** B ({B=básico, I=intermedio, A=avanzado}).

<!-- TODO: justificar nivel con prerequisitos del notebook -->

## 5. Qué funciona bien

- Estructura de **22 secciones** (target 22).
- Cita explícita del schema canónico CAPTIA.
- Helpers `_common` reutilizados (`captia_schema`, `connection`, `plotting`, `synthetic_mocks`).
- Outputs persistidos celda a celda (100.0%).
- `assert`-driven validación.

**Curado:** Convención `^case_[A-J]_(baseline|prod)_\d{4}$` documentada.

## 6. Problemas técnicos

- _Sin bugs P0/P1 conocidos._

**Curado:** P0-3 (Sprint 1 fix parcial): añadido mlflow al group, pero requiere stack para tracking real. En modo offline, fallback JSON activado pero el alumno NO ve UI MLflow.

## 7. Problemas didácticos

**Curado:** Cuesta enseñar MLflow sin servidor. Alternativa: `mlflow ui --backend-store-uri sqlite:///mlruns.db` mencionado pero sin ejecutar en notebook.

## 8. Problemas de reproducibilidad

- verificar manualmente.
- Sin paths absolutos.
- Sin secretos inline.

<!-- TODO: validar `INFLUX_OFFLINE` fallback funciona; idempotencia del setup; determinismo. -->

## 9. Problemas de estilo corporativo CAPTIA.ai

<!-- TODO: comprobar tono, terminología, links a economic_baseline, alineación CENTINELA+. -->

## 10. Problemas de arquitectura Medallion

- **Capa declarada:** transversal.
- **Etapa:** 01 (Bronce → Plata (EDA)).

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

Pedag 4 · Código 5 · Rigor 4 · Visu 4 · Ejer 5 · ErrCom 6 · ROI 5 · Reuso 5 · Coher 5 → **5.0**

## Datasets utilizados

- _(ninguno detectado)_

## Patrones NA-* aplicables

<!-- TODO: marcar cuáles de NA-A..NA-H + NA-01..NA-10 aplican a este notebook concreto -->

## Referencias

- Auditoría detallada: [`../../NOTEBOOK_AUDIT_DETAILED.md`](../../NOTEBOOK_AUDIT_DETAILED.md)
- Auditoría inicial deep-9: [`../../NOTEBOOK_AUDIT.md`](../../NOTEBOOK_AUDIT.md)
- Baseline económico: [`../../../captia/economic_baseline.md`](../../../captia/economic_baseline.md)
- Plan de uso: [`../../NOTEBOOK_PLAN.md`](../../NOTEBOOK_PLAN.md)
- Matriz casos de uso: [`../../USE_CASE_MATRIX.md`](../../USE_CASE_MATRIX.md)
