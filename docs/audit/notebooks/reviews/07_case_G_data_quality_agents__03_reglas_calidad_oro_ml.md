# Review — `notebooks/07_case_G_data_quality_agents/03_reglas_calidad_oro_ml.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** Data Quality + Agents  
> **Etapa:** 03 (Plata → Oro (Features))  
> **Capa Medallion declarada:** oro  
> **Spec:** `docs/specs/synthetic-bms/02-domain-spec.md`  
> **Score:** **8.5 / 10** · Veredicto **B** · Prioridad **OK**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/07_case_G_data_quality_agents/03_reglas_calidad_oro_ml.ipynb` |
| Título | Caso G · 03 Calidad sobre la capa oro (datasets ML) |
| Celdas md / code | 23 / 6 |
| Secciones distintas | 22 |
| Outputs persistidos | 6 / 6 (100.0%) |
| Helpers `_common` | `captia_schema`, `connection`, `plotting`, `synthetic_mocks` |
| Cita schema CAPTIA | sí |
| `assert` presente | sí |
| Mocks etiquetados | — |
| Sin secretos inline | sí |
| Sin paths absolutos | sí |
| Datasets detectados | BDG2 educational (público resampled) |

## 1. Resumen ejecutivo

<!-- AUTO -->
Notebook **03_reglas_calidad_oro_ml** del caso **Data Quality + Agents**, etapa **03** (capa Plata → Oro (Features)). Score **8.5/10**, veredicto **B**. 6/6 celdas de código con outputs persistidos (100.0%). Bugs P0/P1 documentados (ver §6). Helpers `_common` reutilizados: `captia_schema`, `connection`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Caso G · 03 Calidad sobre la capa oro (datasets ML)**.  
KL divergence train vs prod para detectar drift. Threshold operativo KL > 0.1 → warning, > 1.0 → block deploy.

## 3. Caso de uso asociado

- **Dominio:** Data Quality + Agents.
- **Caso CAPTIA Synthetic Data BMS:** `07_case_G_data_quality_agents`.
- **Spec asociado:** `docs/specs/synthetic-bms/02-domain-spec.md`.
- **Capa Medallion:** oro.

## 4. Nivel didáctico esperado

**Nivel:** A ({B=básico, I=intermedio, A=avanzado}).

<!-- TODO: justificar nivel con prerequisitos del notebook -->

## 5. Qué funciona bien

- Estructura de **22 secciones** (target 22).
- Cita explícita del schema canónico CAPTIA.
- Helpers `_common` reutilizados (`captia_schema`, `connection`, `plotting`, `synthetic_mocks`).
- Outputs persistidos celda a celda (100.0%).
- `assert`-driven validación.

**Curado:** Sprint 1 fix de B6 (KL `density=True` → probabilidades + assertion `kl >= -1e-9`).

## 6. Problemas técnicos

- B6: `kl_hist` con `density=True` genera KL negativos (imposible) (Alta)

**Curado:** (resuelto Sprint 1) — bug crítico de probabilidad: histograms `density=True` retornan área=1 no suma=1.

## 7. Problemas didácticos

**Curado:** Lección de Gibbs's inequality: KL ≥ 0 siempre. Si reportas KL negativo, hay bug.

## 8. Problemas de reproducibilidad

- verificar manualmente.
- Sin paths absolutos.
- Sin secretos inline.

<!-- TODO: validar `INFLUX_OFFLINE` fallback funciona; idempotencia del setup; determinismo. -->

## 9. Problemas de estilo corporativo CAPTIA.ai

<!-- TODO: comprobar tono, terminología, links a economic_baseline, alineación CENTINELA+. -->

## 10. Problemas de arquitectura Medallion

- **Capa declarada:** oro.
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

**OK** — mantener.

## 16. Veredicto

**B** — _Bueno, requiere mejora_.

## Scorecard detallado (auditoría deep-9 / Sprints)

Pedag 7 · Código 8 · Rigor 9 · Visu 6 · Ejer 6 · ErrCom 8 · ROI 6 · Reuso 7 · Coher 7 → **7.0**

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
