# .claude — Configuración para CAPTIA-SYNTHETIC-DATA-BMS

Esta carpeta contiene la configuración de agentes, reglas y permisos para Claude Code en este repositorio.

## Estructura

- `agents/` — Subagentes especializados (Markdown con frontmatter YAML).
- `rules/` — Reglas estables del repo (no modificar sin ADR en `09-decision-log.md`).
- `settings.local.json` — Permisos de tooling, env vars, hooks.

## Subagentes disponibles

| Agente | Responsabilidad |
|--------|-----------------|
| `repo-cartographer` | Mapear estructura, dependencias, patrones (read-only) |
| `spec-architect` | Generar/revisar specs SDD en `docs/specs/synthetic-bms/` |
| `infra-reviewer` | Docker, MQTT, Telegraf, InfluxDB, Redis, redes |
| `observability-reviewer` | Prometheus, Loki, Promtail, Grafana, métricas, logs |
| `qa-reviewer` | Tests, determinismo, fixtures, integración, smoke |
| `security-reviewer` | Secretos, env vars, inputs, permisos |

## Reglas activas

- `001-spec-driven-development` — La spec es la fuente de verdad
- `002-captia-canonical-schema` — Measurement / tags / topics inmutables
- `003-vendoring-policy` — `vendor/` es read-only
- `004-docker-compose-conventions` — healthchecks, tags fijos, `${VAR:-default}`
- `005-language-policy` — docs en español, código en inglés

## Política

Cualquier cambio en `.claude/rules/` requiere ADR documentado en `docs/specs/synthetic-bms/09-decision-log.md`.
