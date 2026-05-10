# Review — `notebooks/07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** Data Quality + Agents  
> **Etapa:** 04 (Oro (Modelado))  
> **Capa Medallion declarada:** transversal  
> **Spec:** `docs/specs/synthetic-bms/02-domain-spec.md`  
> **Score:** **8.3 / 10** · Veredicto **B** · Prioridad **P2**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb` |
| Título | Caso G · 04 Agentes especialistas de calidad (mock) |
| Celdas md / code | 23 / 6 |
| Secciones distintas | 22 |
| Outputs persistidos | 6 / 6 (100.0%) |
| Helpers `_common` | `captia_schema`, `connection`, `plotting`, `synthetic_mocks` |
| Cita schema CAPTIA | sí |
| `assert` presente | sí |
| Mocks etiquetados | — |
| Sin secretos inline | sí |
| Sin paths absolutos | sí |
| Datasets detectados | Golden set chatbot (sintético) |

## 1. Resumen ejecutivo

<!-- AUTO -->
Notebook **04_agentes_especialistas_calidad** del caso **Data Quality + Agents**, etapa **04** (capa Oro (Modelado)). Score **8.3/10**, veredicto **B**. 6/6 celdas de código con outputs persistidos (100.0%). Sin bugs P0/P1 reportados. Helpers `_common` reutilizados: `captia_schema`, `connection`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Caso G · 04 Agentes especialistas de calidad (mock)**.  
Agentes con tools tipadas. evaluate_chatbot_response(question, answer, expected_keywords).

## 3. Caso de uso asociado

- **Dominio:** Data Quality + Agents.
- **Caso CAPTIA Synthetic Data BMS:** `07_case_G_data_quality_agents`.
- **Spec asociado:** `docs/specs/synthetic-bms/02-domain-spec.md`.
- **Capa Medallion:** transversal.

## 4. Nivel didáctico esperado

**Nivel:** A ({B=básico, I=intermedio, A=avanzado}).

<!-- TODO: justificar nivel con prerequisitos del notebook -->

## 5. Qué funciona bien

- Estructura de **22 secciones** (target 22).
- Cita explícita del schema canónico CAPTIA.
- Helpers `_common` reutilizados (`captia_schema`, `connection`, `plotting`, `synthetic_mocks`).
- Outputs persistidos celda a celda (100.0%).
- `assert`-driven validación.

**Curado:** Sprint 1 fix de P0-5: `evaluate_chatbot_response` ahora compara con la respuesta real; `validate_silver_layer` computa `df.isna().mean()` + range checks.

## 6. Problemas técnicos

- _Sin bugs P0/P1 conocidos._

**Curado:** (resuelto Sprint 1) — bug semántico: comparaba `expected` con `question` en lugar de con la respuesta.

## 7. Problemas didácticos

**Curado:** Reseña del propio bug en sec 17 (errores comunes) — pedagógicamente potente.

## 8. Problemas de reproducibilidad

- verificar manualmente.
- Sin paths absolutos.
- Sin secretos inline.

<!-- TODO: validar `INFLUX_OFFLINE` fallback funciona; idempotencia del setup; determinismo. -->

## 9. Problemas de estilo corporativo CAPTIA.ai

<!-- TODO: comprobar tono, terminología, links a economic_baseline, alineación CENTINELA+. -->

## 10. Problemas de arquitectura Medallion

- **Capa declarada:** transversal.
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

**P2** — pulido.

## 16. Veredicto

**B** — _Bueno, requiere mejora_.

## Scorecard detallado (auditoría deep-9 / Sprints)

Pedag 8 · Código 7 · Rigor 7 · Visu 6 · Ejer 7 · ErrCom 8 · ROI 7 · Reuso 7 · Coher 7 → **7.1**

## Datasets utilizados

- Golden set chatbot (sintético)

## Patrones NA-* aplicables

<!-- TODO: marcar cuáles de NA-A..NA-H + NA-01..NA-10 aplican a este notebook concreto -->

## Referencias

- Auditoría detallada: [`../../NOTEBOOK_AUDIT_DETAILED.md`](../../NOTEBOOK_AUDIT_DETAILED.md)
- Auditoría inicial deep-9: [`../../NOTEBOOK_AUDIT.md`](../../NOTEBOOK_AUDIT.md)
- Baseline económico: [`../../../captia/economic_baseline.md`](../../../captia/economic_baseline.md)
- Plan de uso: [`../../NOTEBOOK_PLAN.md`](../../NOTEBOOK_PLAN.md)
- Matriz casos de uso: [`../../USE_CASE_MATRIX.md`](../../USE_CASE_MATRIX.md)
