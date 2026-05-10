# Review — `notebooks/05_case_E_weather_solar/04_prediccion_solar.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** Weather + Solar  
> **Etapa:** 04 (Oro (Modelado))  
> **Capa Medallion declarada:** oro  
> **Spec:** `docs/specs/synthetic-bms/02-domain-spec.md`  
> **Score:** **8.7 / 10** · Veredicto **B** · Prioridad **OK**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/05_case_E_weather_solar/04_prediccion_solar.ipynb` |
| Título | Caso E · 04 Predicción solar — clear-sky decomposition + 3 baselines |
| Celdas md / code | 23 / 6 |
| Secciones distintas | 22 |
| Outputs persistidos | 6 / 6 (100.0%) |
| Helpers `_common` | `captia_schema`, `connection`, `diagnostic_plots`, `eval_helpers`, `plotting`, `synthetic_mocks` |
| Cita schema CAPTIA | sí |
| `assert` presente | sí |
| Mocks etiquetados | — |
| Sin secretos inline | sí |
| Sin paths absolutos | sí |
| Datasets detectados | ERA5 Xàtiva (público mockeado), Golden set chatbot (sintético) |

## 1. Resumen ejecutivo

<!-- AUTO -->
Notebook **04_prediccion_solar** del caso **Weather + Solar**, etapa **04** (capa Oro (Modelado)). Score **8.7/10**, veredicto **B**. 6/6 celdas de código con outputs persistidos (100.0%). Sin bugs P0/P1 reportados. Helpers `_common` reutilizados: `captia_schema`, `connection`, `diagnostic_plots`, `eval_helpers`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Caso E · 04 Predicción solar — clear-sky decomposition + 3 baselines**.  
Top-4 (8.6/10). Clear-sky decomposition + 4 baselines (climatología por hora, persistencia 1h, clear-sky, RF) con skill score.

## 3. Caso de uso asociado

- **Dominio:** Weather + Solar.
- **Caso CAPTIA Synthetic Data BMS:** `05_case_E_weather_solar`.
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

**Curado:** Clip a 0 + máscara nocturna (Sprint 2 fix de P1-4). Climatología por hora bate a RF en 720 horas — lección dura.

## 6. Problemas técnicos

- _Sin bugs P0/P1 conocidos._

**Curado:** Sec 19 LaTeX (clear-sky model) parcialmente conectada al código (Sprint 2 cubrió la fórmula principal).

## 7. Problemas didácticos

**Curado:** Antes de invertir en GPU, prueba climatología. Insight contraintuitivo bien presentado.

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

Pedag 9 · Código 9 · Rigor 8 · Visu 8 · Ejer 8 · ErrCom 8 · ROI 8 · Reuso 9 · Coher 9 → **8.6**

## Datasets utilizados

- ERA5 Xàtiva (público mockeado)
- Golden set chatbot (sintético)

## Patrones NA-* aplicables

<!-- TODO: marcar cuáles de NA-A..NA-H + NA-01..NA-10 aplican a este notebook concreto -->

## Referencias

- Auditoría detallada: [`../../NOTEBOOK_AUDIT_DETAILED.md`](../../NOTEBOOK_AUDIT_DETAILED.md)
- Auditoría inicial deep-9: [`../../NOTEBOOK_AUDIT.md`](../../NOTEBOOK_AUDIT.md)
- Baseline económico: [`../../../captia/economic_baseline.md`](../../../captia/economic_baseline.md)
- Plan de uso: [`../../NOTEBOOK_PLAN.md`](../../NOTEBOOK_PLAN.md)
- Matriz casos de uso: [`../../USE_CASE_MATRIX.md`](../../USE_CASE_MATRIX.md)
