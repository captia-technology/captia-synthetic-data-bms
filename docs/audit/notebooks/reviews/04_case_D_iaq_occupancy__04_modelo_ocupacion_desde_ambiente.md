# Review — `notebooks/04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** IAQ + Occupancy  
> **Etapa:** 04 (Oro (Modelado))  
> **Capa Medallion declarada:** oro  
> **Spec:** `docs/specs/synthetic-bms/02-domain-spec.md`  
> **Score:** **9.6 / 10** · Veredicto **A** · Prioridad **OK**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente.ipynb` |
| Título | Caso D · 04 Modelo de ocupación desde ambiente — analítico vs ML |
| Celdas md / code | 23 / 6 |
| Secciones distintas | 22 |
| Outputs persistidos | 6 / 6 (100.0%) |
| Helpers `_common` | `captia_schema`, `connection`, `diagnostic_plots`, `eval_helpers`, `plotting`, `synthetic_mocks` |
| Cita schema CAPTIA | sí |
| `assert` presente | sí |
| Mocks etiquetados | — |
| Sin secretos inline | sí |
| Sin paths absolutos | sí |
| Datasets detectados | Golden set chatbot (sintético), In-Gauge AULA01 (sintético) |

## 1. Resumen ejecutivo

<!-- AUTO -->
Notebook **04_modelo_ocupacion_desde_ambiente** del caso **IAQ + Occupancy**, etapa **04** (capa Oro (Modelado)). Score **9.6/10**, veredicto **A**. 6/6 celdas de código con outputs persistidos (100.0%). Bugs P0/P1 documentados (ver §6). Helpers `_common` reutilizados: `captia_schema`, `connection`, `diagnostic_plots`, `eval_helpers`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Caso D · 04 Modelo de ocupación desde ambiente — analítico vs ML**.  
Top-1 del repo (9.5/10). 3 baselines (threshold trivial / balance de masa físico / RandomForest balanceado) con TSS(5) + class_weight + IC bootstrap.

## 3. Caso de uso asociado

- **Dominio:** IAQ + Occupancy.
- **Caso CAPTIA Synthetic Data BMS:** `04_case_D_iaq_occupancy`.
- **Spec asociado:** `docs/specs/synthetic-bms/02-domain-spec.md`.
- **Capa Medallion:** oro.

## 4. Nivel didáctico esperado

**Nivel:** A ({B=básico, I=intermedio, A=avanzado}).

<!-- TODO: justificar nivel con prerequisitos del notebook -->

## 5. Qué funciona bien

- Estructura de **22 secciones** (target 22).
- Cita explícita del schema canónico CAPTIA.
- Helpers `_common` reutilizados (`captia_schema`, `connection`, `diagnostic_plots`, `eval_helpers`, `plotting`, `synthetic_mocks`).
- Outputs persistidos celda a celda (100.0%).
- `assert`-driven validación.

**Curado:** Patrón Top-1: threshold → balance físico → RF. `assert y_te.sum() > 0` blindado. CV temporal. class_weight balanced. Mock 30 días.

## 6. Problemas técnicos

- P0 (resuelto Sprint 1): F1=0 con 7 días + split 70/30 → ahora 30 días + class_weight + TSS

**Curado:** Resuelto en Sprint 1 (era F1=0 con mock 7 días + split 70/30, P0-1).

## 7. Problemas didácticos

**Curado:** Demuestra que un modelo físico calibrado puede batir a un RF mal alimentado. Lección dura y memorable.

## 8. Problemas de reproducibilidad

- verificar manualmente.
- Sin paths absolutos.
- Sin secretos inline.

<!-- TODO: validar `INFLUX_OFFLINE` fallback funciona; idempotencia del setup; determinismo. -->

## 9. Problemas de estilo corporativo CAPTIA.ai

<!-- TODO: comprobar tono, terminología, links a economic_baseline, alineación CENTINELA+. -->

## 10. Problemas de arquitectura Medallion

- **Capa declarada:** oro.
- **Etapa:** 04 (Oro (Modelado)).

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

**A** — _Excelente, solo ajustes menores_.

## Scorecard detallado (auditoría deep-9 / Sprints)

Pedag 10 · Código 10 · Rigor 10 · Visu 9 · Ejer 9 · ErrCom 9 · ROI 9 · Reuso 10 · Coher 10 → **9.5**

## Datasets utilizados

- Golden set chatbot (sintético)
- In-Gauge AULA01 (sintético)

## Patrones NA-* aplicables

<!-- TODO: marcar cuáles de NA-A..NA-H + NA-01..NA-10 aplican a este notebook concreto -->

## Referencias

- Auditoría detallada: [`../../NOTEBOOK_AUDIT_DETAILED.md`](../../NOTEBOOK_AUDIT_DETAILED.md)
- Auditoría inicial deep-9: [`../../NOTEBOOK_AUDIT.md`](../../NOTEBOOK_AUDIT.md)
- Baseline económico: [`../../../captia/economic_baseline.md`](../../../captia/economic_baseline.md)
- Plan de uso: [`../../NOTEBOOK_PLAN.md`](../../NOTEBOOK_PLAN.md)
- Matriz casos de uso: [`../../USE_CASE_MATRIX.md`](../../USE_CASE_MATRIX.md)
