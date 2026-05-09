# 01 — Product spec

## Context

CAPTIA Technology necesita un microservicio dedicado a la generación de datos sintéticos BMS (Building Management System, aulas educativas IES Simarro) para soportar 11 casos de uso educativos definidos en `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md`. Los datos reales en `simarro-prod` son aún insuficientes (poco histórico, fallos no etiquetados). El microservicio debe ser autocontenido, demo-able y producir datasets reproducibles.

## Goal

Construir `CAPTIA-SYNTHETIC-DATA-BMS` como microservicio en vivo, con stack Docker autónomo, que:

1. Genere y publique a MQTT telemetría sintética conforme al schema canónico CAPTIA.
2. Soporte backfill 1-12 meses con `seed=42` reproducible.
3. Inyecte fallos HVAC etiquetados para Caso C.
4. Exponga API HTTP para control y export de datasets.
5. Provea dashboards Grafana provisionados.

## Non-goals (fuera de v1)

- Caso E (meteorología ERA5): cada equipo descarga directamente.
- Caso F (Big Data Spark benchmarks).
- Caso G (auditoría calidad sobre datos reales `simarro-prod`).
- Caso H (chatbot RAG): consume modelos entrenados desde Casos B/C/E.
- Caso I (datasets construcción BDG2).
- Caso J (visión artificial DGT).
- Caso K (fuera de alcance).
- UI custom (se usa Grafana provisionado).
- Calibración con datos reales del IES Simarro (hooks dejados para post-v1).
- Anonimización de dump real.

## Stakeholders

| Rol | Persona / Equipo | Interés |
|-----|------------------|---------|
| Producto | CAPTIA Technology (Jaume Albert) | Mantener alineación con CENTINELA+ |
| Consumidor docente | Profesores IES Simarro | Datos sintéticos para clase |
| Consumidor alumno | Equipos de alumnos | Entrenamiento ML (Casos B, C, D) |
| Mantenedor | Equipo CAPTIA | DevOps + soporte |

## Use cases v1

### UC-A — Pipeline IoT en vivo (Caso A)

- **Actor**: profesor / alumno.
- **Escenario**: lanza `task up` y `POST /v1/control/start {mode:"live"}`.
- **Resultado**: en ≤ 90 s todos los servicios `healthy`; en < 1 min se ven datos fluyendo en Grafana.
- **Trazabilidad**: RF-01, RF-02, RF-03, RF-05, RNF-01, RNF-02.

### UC-B — Backfill 12 meses para predicción consumo (Caso B)

- **Actor**: equipo alumno entrenando modelo SARIMA/XGBoost.
- **Escenario**: `POST /v1/datasets/export {months:12, format:"line_protocol"}`.
- **Resultado**: archivo `.lp` con ≥ 10 aulas × 12 meses de telemetría; restaurable en bucket `telemetry_1h`.
- **Trazabilidad**: RF-01, RF-04, RF-07, RF-08, RF-12.

### UC-C — Backfill con fallos para detección anomalías (Caso C)

- **Actor**: equipo alumno entrenando Isolation Forest / Autoencoder.
- **Escenario**: `POST /v1/datasets/export {months:6, include_faults:true}`.
- **Resultado**: dataset incluye ≥ 4 tipos de fallos en bucket `state_events` con `variable=fault.<tipo>`.
- **Trazabilidad**: RF-09, RNF-07.

### UC-D — Dataset 1min calidad aire / ocupación (Caso D)

- **Actor**: equipo alumno entrenando modelo ocupancia desde CO2.
- **Escenario**: `POST /v1/datasets/export` con config `bms_v1_caseD_iaq.yaml`.
- **Resultado**: dataset 1-3 meses a frecuencia 1min con CO2 + Tª + RH + sound + lux + occupancy.
- **Trazabilidad**: RF-04, RF-07, RF-08.

## Constraints

- **Plataforma**: Docker Compose v2, Linux/Windows host.
- **Lenguaje**: Python 3.12+.
- **Schema**: canónico CAPTIA inmutable (`captia_point` + 5 tags + field `value`).
- **Determinismo**: `seed=42` por defecto.
- **Idioma**: docs en español, código en inglés.
- **Seguridad**: sin secretos hardcodeados.
- **Plazo objetivo**: alineado con curso lectivo 2025-2026 IES Simarro.

## Acceptance criteria

| ID | Criterio | Cómo se valida |
|----|----------|---------------|
| AC-01 | `task up` levanta stack en ≤ 90 s; todos los servicios `healthy`. | `docker compose ps --format '{{.Name}} {{.Status}}'` muestra `healthy`. |
| AC-02 | `task smoke` valida MQTT publish + Influx query + Grafana healthz. | Exit code 0. |
| AC-03 | 1 hora live mode publica ≥ 700 puntos/aula·hora con `seed=42` reproducible. | Query Flux contar puntos; 2 ejecuciones con mismo seed dan mismos hash de muestreo. |
| AC-04 | `POST /v1/datasets/export {months:12}` genera dump line-protocol válido en < 30 min. | Archivo `.lp` no vacío + `head -1` cumple sintaxis line-protocol. |
| AC-05 | Caso C contiene ≥ 4 tipos de fallos etiquetados en `state_events`. | Query Flux por `variable=~"fault\\..*"` muestra 4 tipos. |
| AC-06 | `ruff check` y `ruff format --check` PASS sin warnings. | Exit code 0. |
| AC-07 | `pytest -m unit` y `pytest -m integration` PASS. | Exit code 0. |
| AC-08 | Schema canónico CAPTIA respetado en todas las publicaciones MQTT. | `scripts/verify_canonical_schema.sh` PASS. |
| AC-09 | Cobertura `bms_data_generator` ≥ 80% líneas. | `pytest --cov` reporta ≥ 80%. |
| AC-10 | Sin secretos hardcodeados en código fuente o `.env.example`. | `git grep -nE "password=|token=" -- ':!.env.example'` vacío. |

## Success metrics post-v1

- Tiempo de onboarding para alumno: `git clone` → primer dato visible en Grafana ≤ 10 min.
- Reproducibilidad: mismo `seed` produce datasets idénticos (hash sha256).
- Mantenibilidad: añadir nuevo dominio (ej. `bms_industrial`) no requiere modificar `vendor/` ni `core/`.

## Traceability

| Requisito | Tareas asociadas | Tests |
|-----------|-----------------|-------|
| RF-01..RF-12 | Fases 4-9 | `tests/integration/test_canonical_schema.py`, `tests/e2e/test_dump_caseB.py` |
| RNF-01..RNF-12 | Fases 5-7 | Tests de performance, smoke |
| AC-01..AC-10 | Fase 10 | Validation checklist |
