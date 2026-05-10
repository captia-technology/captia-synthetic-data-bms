# Review — `notebooks/08_case_H_rag_chatbot/04_rag_documental.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** RAG + Chatbot  
> **Etapa:** 04 (Oro (Modelado))  
> **Capa Medallion declarada:** oro  
> **Spec:** `docs/specs/synthetic-bms/01-product-spec.md`  
> **Score:** **8.8 / 10** · Veredicto **B** · Prioridad **OK**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/08_case_H_rag_chatbot/04_rag_documental.ipynb` |
| Título | Caso H · 04 RAG documental — TF-IDF como sustituto ligero de embeddings |
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
Notebook **04_rag_documental** del caso **RAG + Chatbot**, etapa **04** (capa Oro (Modelado)). Score **8.8/10**, veredicto **B**. 6/6 celdas de código con outputs persistidos (100.0%). Bugs P0/P1 documentados (ver §6). Helpers `_common` reutilizados: `captia_schema`, `connection`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Caso H · 04 RAG documental — TF-IDF como sustituto ligero de embeddings**.  
Top-3 (8.7/10). RAG con TF-IDF español sobre 12 docs. Recall@3=0.91, MRR + golden set 13 preguntas.

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
- Outputs persistidos celda a celda (100.0%).
- `assert`-driven validación.

**Curado:** Sprint 1 fix de B2 (clave duplicada en `expected_map` → 13 únicas con `assert len(expected_map) == 13`). Heatmap cosine_similarity con insight real.

## 6. Problemas técnicos

- B2: clave duplicada en `expected_map` ("¿Qué es el bucket telemetry_1h?" 2 veces) (Alta)

**Curado:** Faltan secs 19/20/21 según NOTEBOOK_AUDIT.md (P1-3) — pendiente revisar tras Sprint 4.

## 7. Problemas didácticos

**Curado:** TF-IDF bate Sentence-Transformers en latencia (2 ms vs 50 ms) y RAM (50 MB vs 2.3 GB) para corpus pequeños. Decisión Pareto-óptima.

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

**B** — _Bueno, requiere mejora_.

## Scorecard detallado (auditoría deep-9 / Sprints)

Pedag 9 · Código 9 · Rigor 9 · Visu 9 · Ejer 8 · ErrCom 8 · ROI 8 · Reuso 9 · Coher 9 → **8.7**

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
