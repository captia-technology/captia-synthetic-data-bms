# STATUS — synthetic-bms

**Última actualización**: 2026-05-09
**Fase actual**: 10 (Tests E2E + validación) — COMPLETADA
**Tarea en curso**: ninguna
**Última tarea completada**: T-051 (validación final lint + tests)
**Tests verdes**: 44 PASS (32 unit + 11 integration + 1 snapshot), 0 failed
**Bloqueos**: ninguno
**Próxima tarea**: post-v1 — calibración real (L-01) + revisión cruzada por subagentes

## Histórico

| Fecha | Hito |
|-------|------|
| 2026-05-09 | Inicio Fase 0. Bootstrap repo + `.claude` config (T-001..T-007) |
| 2026-05-09 | Fin Fase 0. Inicio Fase 1 |
| 2026-05-09 | Fin Fase 1 (research docs 00-*). Inicio Fase 2 |
| 2026-05-09 | Fin Fase 2 (specs SDD 01-10). Inicio Fase 3 |
| 2026-05-09 | Fin Fase 3 (vendoring synthetic-generator). Inicio Fase 4 |
| 2026-05-09 | Fin Fase 4 (extensions bms_calibration). Inicio Fase 5 |
| 2026-05-09 | Fin Fase 5 (microservicio FastAPI). Inicio Fase 6 |
| 2026-05-09 | Fin Fase 6 (Docker infra). Inicio Fase 7 |
| 2026-05-09 | Fin Fase 7 (4 configs scenario). Inicio Fase 8 |
| 2026-05-09 | Fin Fase 8 (4 dashboards Grafana). Inicio Fase 9 |
| 2026-05-09 | Fin Fase 9 (Taskfile + scripts). Inicio Fase 10 |
| 2026-05-09 | Fin Fase 10. v1 lista para revisión cruzada |

## Métricas v1

- **Commits**: 18 (uno por tarea principal).
- **Archivos creados**: ≈ 200 (incl. vendor).
- **Líneas escritas (excl. vendor)**: ≈ 4500 (specs + código + configs).
- **Tests verdes**: 44.
- **Lint**: ruff check + format check PASS.
- **Workspace `uv sync`**: OK (43 packages).

## Decisiones nuevas (post-plan inicial)

- **2026-05-09**: añadido `[dependency-groups] dev` y `dependencies` explícitas al `pyproject.toml` raíz para que `uv sync` instale los miembros del workspace.
- **2026-05-09**: `addopts="--import-mode=importlib"` en pytest config para evitar colisión de conftest entre paquetes del workspace.
- **2026-05-09**: ignorar regla `UP042` (StrEnum) en ruff para mantener compatibilidad explícita.

## Pendientes post-v1

1. **Calibración real (L-01)**: cuando CAPTIA Technology proporcione parámetros calibrados, sobrescribir en `extensions/bms_calibration/physics_overrides.py` y registrar como ADR-016.
2. **Wiring runner**: `RunnerService.start()` y `DumpService.export()` actualmente son esqueletos; integrar con `vendor.synthetic_generator.core.runner.ScenarioRunner` en thread/proceso.
3. **Tests E2E con stack levantado**: ejecutar `task up && task smoke && pytest -m smoke` para validar pipeline completo end-to-end.
4. **Revisión cruzada por subagentes**: lanzar `infra-reviewer`, `observability-reviewer`, `qa-reviewer`, `security-reviewer`, `spec-architect` en sesión separada.
5. **`influxdb-simarro-buckets.pptx` y `captia-connect-partner-integration.pptx`**: parsear si aportan información adicional al schema.

## Próximos pasos recomendados

1. Probar `task up` en máquina de desarrollo (Docker corriendo).
2. Smoke test completo (`task smoke` post `task wait:healthy`).
3. Revisión cruzada por subagentes en sesión separada.
4. Tagging `v0.1.0`.
