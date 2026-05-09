# CLAUDE.md — CAPTIA-SYNTHETIC-DATA-BMS

Microservicio generador de datos sintéticos BMS (Building Management System, aulas IES Simarro) para CAPTIA.

## Quick context
- **Dominio**: aulas educativas IES Simarro, schema canónico CAPTIA (`captia_point` + 5 tags + field `value`).
- **Arquitectura**: microservicio FastAPI (`modules/bms-data-generator`) que orquesta generador hexagonal vendorizado (`vendor/synthetic-generator`) más calibración local (`extensions/bms_calibration`).
- **Stack**: Mosquitto, Telegraf, InfluxDB 2.7, Redis 7, Grafana 11.4, Prometheus, Loki, Promtail. Red `captia-network`.
- **Python**: 3.12+ con uv + ruff + pytest.

## Reglas de oro (ver `.claude/rules/` para detalle completo)

1. **Spec-driven**: la especificación es la fuente de verdad. Leer `docs/specs/synthetic-bms/` antes de codificar.
2. **Schema canónico CAPTIA inviolable**: nunca cambiar measurement / tags / topics. Ver `.claude/rules/002-captia-canonical-schema.md`.
3. **Vendoring read-only**: `vendor/synthetic-generator/` no se modifica; toda extensión va en `extensions/` o `modules/`.
4. **Determinismo**: `seed=42` por defecto, `numpy.random.default_rng(seed)` (no `np.random.seed()`).
5. **Sin secretos en código**; solo `.env.example` documentado con `CHANGE_ME`.
6. **Healthchecks** en todos los servicios; tags Docker fijos; `${VAR:-default}`.
7. **Idioma**: docs en español, identificadores en inglés (excepción: claves CAPTIA).

## Skills y agentes

- Subagentes en `.claude/agents/`: `repo-cartographer`, `spec-architect`, `infra-reviewer`, `observability-reviewer`, `qa-reviewer`, `security-reviewer`.
- Reglas estables: `.claude/rules/`.
- Permisos: `.claude/settings.local.json`.

## Comandos clave

| Comando | Propósito |
|---------|-----------|
| `task install` | `uv sync` workspace |
| `task lint` | Ruff check + format check |
| `task test` | Pytest unit |
| `task test:integration` | Pytest integration |
| `task up` | Levantar stack completo |
| `task down` | Detener stack |
| `task smoke` | Healthcheck endpoints + verify schema |
| `task dump:caseB` | Generar dump 12 meses Caso B |

## Spec source of truth

Antes de cualquier cambio relevante, leer `@docs/specs/synthetic-bms/01-product-spec.md` y la spec asociada al cambio (02..10).

## NO hacer

- No usar `latest` en imágenes Docker.
- No usar `print()` en producción; logging estructurado JSON.
- No mezclar dominio, sinks e infraestructura en un solo módulo.
- No introducir dependencias sin actualizar `pyproject.toml` y `09-decision-log.md`.
- No commit con `--no-verify`.
- No editar archivos en `vendor/synthetic-generator/` (read-only).

## Casos de uso v1

- **Caso A**: Pipeline IoT en vivo (MQTT → Telegraf → InfluxDB → Grafana).
- **Caso B**: Backfill 12 meses para predicción consumo eléctrico.
- **Caso C**: Backfill con fallos HVAC etiquetados para detección de anomalías.
- **Caso D**: Dataset 1min de calidad aire / ocupación.

Ver `docs/specs/synthetic-bms/01-product-spec.md` para criterios de aceptación.
