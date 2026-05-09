# 10 — Validation checklist (final)

> Marca `[x]` cuando se valide. Si una validación falla, abrir tarea de fix y bloquear merge.

## Calidad

- [x] `task lint` (ruff check + format check) PASS sin warnings.
- [x] `task test` (unit) PASS — 32 tests.
- [x] `task test:integration` (in-process) PASS — 11 tests.
- [ ] `task test:smoke` PASS post-up.
- [x] `task test:snapshot` PASS (seed=42 determinista — anchor `de6c4e49…b56ae66`).
- [ ] Cobertura `bms_data_generator` ≥ 80% líneas (`pytest --cov`).

## Seguridad

- [ ] `git grep -nE "password=|token=" -- ':!.env.example' ':!docs'` no muestra valores reales.
- [ ] `.env` está en `.gitignore` (verificado por tests CI).
- [ ] CORS configurado conscientemente.
- [ ] `BMS_API_TOKEN` requerido en `/v1/*`.
- [ ] Sin `eval`, `exec`, `pickle.load` con datos no confiables.
- [ ] Healthcheck endpoints sin info sensible (no version interna, no env vars).

## Arquitectura

- [ ] `vendor/synthetic-generator/` no modificado tras snapshot inicial (`git diff vendor/synthetic-generator/` vacío salvo PATCHES/).
- [ ] `core/` no importa `domains/` ni `sinks/`:
  ```bash
  grep -r "from synthetic_generator.domains\|from synthetic_generator.sinks" vendor/synthetic-generator/src/synthetic_generator/core/
  ```
  → vacío.
- [ ] `extensions/bms_calibration/` no importa `vendor/synthetic-generator/sinks/` ni `vendor/synthetic-generator/domains/bms_classrooms/physics/`.

## Infraestructura

- [ ] `task up` completa en ≤ 90 s; `docker compose ps` muestra todos `(healthy)`.
- [ ] Tags Docker fijos (no `latest`):
  ```bash
  grep -nE "image:.*:latest" compose/*.yaml
  ```
  → vacío (excepto build local).
- [ ] Variables `${VAR:-default}` en compose (excepto `:?required`).
- [ ] `depends_on: condition: service_healthy` en consumidores.
- [ ] Red `captia-network` declarada y compartida.
- [ ] 6 buckets InfluxDB creados: `influx bucket list`.
- [ ] 5 tareas Flux activas: `influx task list`.

## Observabilidad

- [ ] `/metrics` devuelve formato Prometheus con métricas `captia_bms_*`.
- [ ] Logs JSON estructurados (`docker logs captia-bms-generator | head -1 | python -c "import sys,json; json.loads(sys.stdin.read())"`).
- [ ] Dashboards Grafana provisionados (4 visibles).
- [ ] Alertas Prometheus configuradas (`bms_alerts` group).
- [ ] Promtail captura logs en Loki (`{compose_project="captia-bms"}` retorna entradas).

## Schema canónico CAPTIA

- [ ] `scripts/verify_canonical_schema.sh` PASS.
- [ ] Topics MQTT exactos: `captia/{env}/{tenant}/{site}/{device}/telemetry/{name}` (verificable con `mosquitto_sub`).
- [ ] Measurement = `captia_point` (verificable con Flux query).
- [ ] 5 tags: `captia_env`, `domain_id`, `site_id`, `asset_id`, `variable`.
- [ ] Field = `value` (float).
- [ ] Bucket `captia_metadata` poblado para todas las variables.

## Casos de uso

- [ ] **Caso A** (Pipeline IoT en vivo): `task up` + control/start → datos en Grafana en < 2 min.
- [ ] **Caso B** (Backfill 12m): `task dump:caseB` produce archivo `.lp` en `output/` < 30 min.
- [ ] **Caso C** (Fallos HVAC): dump con `include_faults=true` contiene 4 tipos en `state_events`.
- [ ] **Caso D** (Calidad aire 1min): config `caseD` produce dataset 1-3 meses con CO2 cíclico.

## Documentación

- [ ] `README.md` raíz tiene quickstart funcional.
- [ ] `STATUS.md` actualizado con última fase completa.
- [ ] `09-decision-log.md` contiene ADR-001..ADR-015 (más eventuales ADR-016+).
- [ ] `00-open-questions.md` tiene estado actualizado.
- [ ] Sin TODOs sin trazar en código (`grep -rn "TODO\\|FIXME" modules/ extensions/`).

## Revisión cruzada

- [ ] `infra-reviewer` veredicto PASS o PASS_WITH_NOTES.
- [ ] `observability-reviewer` veredicto PASS o PASS_WITH_NOTES.
- [ ] `qa-reviewer` veredicto PASS o PASS_WITH_NOTES.
- [ ] `security-reviewer` veredicto PASS o PASS_WITH_NOTES.
- [ ] `spec-architect` veredicto PASS o PASS_WITH_NOTES.

## Final

- [ ] `STATUS.md` actualizado con "v1 ready for review" / "v1 released".
- [ ] Tag git `v0.1.0` aplicado tras checklist completa.
