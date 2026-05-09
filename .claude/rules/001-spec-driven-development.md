# Regla 001 — Spec-Driven Development

## Principio

La especificación es la fuente de verdad. Toda implementación deriva de una spec en `docs/specs/synthetic-bms/`.

## Aplicación

1. Antes de codificar, leer la spec asociada (01..10).
2. Cada tarea de `08-task-plan.md` referencia un RF/RNF.
3. Cada cambio en API o schema requiere actualizar `06-api-and-ui-spec.md` o `02-domain-spec.md`.
4. Decisiones técnicas se registran en `09-decision-log.md` con formato ADR.
5. `STATUS.md` se actualiza tras cada tarea completa.

## Anti-patrón

- Implementar features sin spec previa.
- Modificar specs sin propagar cambios al plan/tareas/tests.
- Documentar specs después del código (post-rationalización).
