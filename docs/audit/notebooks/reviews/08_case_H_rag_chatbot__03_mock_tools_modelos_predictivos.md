# Review — `notebooks/08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** RAG + Chatbot  
> **Etapa:** 03 (Plata → Oro (Features))  
> **Capa Medallion declarada:** oro  
> **Spec:** `docs/specs/synthetic-bms/01-product-spec.md`  
> **Score:** **7.8 / 10** · Veredicto **C** · Prioridad **P2**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos.ipynb` |
| Título | Caso H · 03 Tools mock para modelos predictivos |
| Celdas md / code | 23 / 4 |
| Secciones distintas | 22 |
| Outputs persistidos | 3 / 4 (75.0%) |
| Helpers `_common` | `captia_schema`, `connection`, `plotting`, `synthetic_mocks` |
| Cita schema CAPTIA | sí |
| `assert` presente | NO |
| Mocks etiquetados | — |
| Sin secretos inline | sí |
| Sin paths absolutos | sí |
| Datasets detectados | Golden set chatbot (sintético) |

## 1. Resumen ejecutivo

<!-- AUTO -->
Notebook **03_mock_tools_modelos_predictivos** del caso **RAG + Chatbot**, etapa **03** (capa Plata → Oro (Features)). Score **7.8/10**, veredicto **C**. 3/4 celdas de código con outputs persistidos (75.0%). Sin bugs P0/P1 reportados. Helpers `_common` reutilizados: `captia_schema`, `connection`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Caso H · 03 Tools mock para modelos predictivos**.  
_(Inferido de la sec 1 y 2 del notebook; ampliar a 5-7 líneas con objetivo declarado vs inferido)_

## 3. Caso de uso asociado

- **Dominio:** RAG + Chatbot.
- **Caso CAPTIA Synthetic Data BMS:** `08_case_H_rag_chatbot`.
- **Spec asociado:** `docs/specs/synthetic-bms/01-product-spec.md`.
- **Capa Medallion:** oro.

## 4. Nivel didáctico esperado

**Nivel:** A ({B=básico, I=intermedio, A=avanzado}).

<!-- TODO: justificar nivel con prerequisitos del notebook -->

## 5. Qué funciona bien

- Estructura de **22 secciones** (target 22).
- Cita explícita del schema canónico CAPTIA.
- Helpers `_common` reutilizados (`captia_schema`, `connection`, `plotting`, `synthetic_mocks`).
- _(outputs persistidos parciales)_
- _(sin asserts visibles)_

_(curador: añadir 2-3 puntos cualitativos del notebook)_

## 6. Problemas técnicos

- _Sin bugs P0/P1 conocidos._

_(curador: ampliar con problemas específicos detectados al leer el notebook)_

## 7. Problemas didácticos

_(curador: revisar si secs 12-17 explican el porqué, no solo el qué; mini-conclusiones, errores comunes, ejercicios)_

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

**P2** — pulido.

## 16. Veredicto

**C** — _Útil pero necesita refactor serio_.

## Scorecard detallado (auditoría deep-9 / Sprints)

_(no en deep-9; ver agregados en NOTEBOOK_QUALITY_MATRIX.md)_

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
