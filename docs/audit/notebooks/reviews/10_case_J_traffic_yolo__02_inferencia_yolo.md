# Review — `notebooks/10_case_J_traffic_yolo/02_inferencia_yolo.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** Computer Vision  
> **Etapa:** 02 (Bronce → Plata (ETL))  
> **Capa Medallion declarada:** bronce → plata  
> **Spec:** `docs/specs/synthetic-bms/01-product-spec.md`  
> **Score:** **8.0 / 10** · Veredicto **B** · Prioridad **P2**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/10_case_J_traffic_yolo/02_inferencia_yolo.ipynb` |
| Título | Caso J · 02 Inferencia YOLO (mock por defecto) |
| Celdas md / code | 23 / 6 |
| Secciones distintas | 22 |
| Outputs persistidos | 5 / 6 (83.3%) |
| Helpers `_common` | `captia_schema`, `connection`, `plotting`, `synthetic_mocks` |
| Cita schema CAPTIA | sí |
| `assert` presente | sí |
| Mocks etiquetados | — |
| Sin secretos inline | sí |
| Sin paths absolutos | sí |
| Datasets detectados | DGT cameras (sintético) |

## 1. Resumen ejecutivo

<!-- AUTO -->
Notebook **02_inferencia_yolo** del caso **Computer Vision**, etapa **02** (capa Bronce → Plata (ETL)). Score **8.0/10**, veredicto **B**. 5/6 celdas de código con outputs persistidos (83.3%). Bugs P0/P1 documentados (ver §6). Helpers `_common` reutilizados: `captia_schema`, `connection`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Caso J · 02 Inferencia YOLO (mock por defecto)**.  
Bottom-2 (3.5/10). YOLO mock determinista con SHA-256 (no JPEG magic).

## 3. Caso de uso asociado

- **Dominio:** Computer Vision.
- **Caso CAPTIA Synthetic Data BMS:** `10_case_J_traffic_yolo`.
- **Spec asociado:** `docs/specs/synthetic-bms/01-product-spec.md`.
- **Capa Medallion:** bronce → plata.

## 4. Nivel didáctico esperado

**Nivel:** I ({B=básico, I=intermedio, A=avanzado}).

<!-- TODO: justificar nivel con prerequisitos del notebook -->

## 5. Qué funciona bien

- Estructura de **22 secciones** (target 22).
- Cita explícita del schema canónico CAPTIA.
- Helpers `_common` reutilizados (`captia_schema`, `connection`, `plotting`, `synthetic_mocks`).
- Outputs persistidos celda a celda (83.3%).
- `assert`-driven validación.

**Curado:** Sprint 1 fix de B4 + B5: `hashlib.sha256(image_bytes).digest()[:4]` + `image_seed` parametrizado.

## 6. Problemas técnicos

- B4: `count_vehicles_mock` usa `image_bytes[:4]` (JPEG magic) → 5 imágenes producen output idéntico (Alta)

**Curado:** (resuelto Sprint 1) — B4: `count_vehicles_mock` usaba `image_bytes[:4]` (JPEG magic común FF D8 FF E0) → 5 imágenes producían output idéntico.

## 7. Problemas didácticos

**Curado:** Bug clásico de mocks: usar magic bytes como seed. Lección memorable.

## 8. Problemas de reproducibilidad

- verificar manualmente.
- Sin paths absolutos.
- Sin secretos inline.

<!-- TODO: validar `INFLUX_OFFLINE` fallback funciona; idempotencia del setup; determinismo. -->

## 9. Problemas de estilo corporativo CAPTIA.ai

<!-- TODO: comprobar tono, terminología, links a economic_baseline, alineación CENTINELA+. -->

## 10. Problemas de arquitectura Medallion

- **Capa declarada:** bronce → plata.
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

Pedag 4 · Código 3 · Rigor 3 · Visu 4 · Ejer 4 · ErrCom 5 · ROI 4 · Reuso 4 · Coher 4 → **3.5** (pre-Sprint 1)

## Datasets utilizados

- DGT cameras (sintético)

## Patrones NA-* aplicables

<!-- TODO: marcar cuáles de NA-A..NA-H + NA-01..NA-10 aplican a este notebook concreto -->

## Referencias

- Auditoría detallada: [`../../NOTEBOOK_AUDIT_DETAILED.md`](../../NOTEBOOK_AUDIT_DETAILED.md)
- Auditoría inicial deep-9: [`../../NOTEBOOK_AUDIT.md`](../../NOTEBOOK_AUDIT.md)
- Baseline económico: [`../../../captia/economic_baseline.md`](../../../captia/economic_baseline.md)
- Plan de uso: [`../../NOTEBOOK_PLAN.md`](../../NOTEBOOK_PLAN.md)
- Matriz casos de uso: [`../../USE_CASE_MATRIX.md`](../../USE_CASE_MATRIX.md)
