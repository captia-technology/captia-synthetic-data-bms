# 06 — API and UI spec

## Context

El microservicio expone un control plane HTTP minimalista vía FastAPI y delega la UI de monitorización a Grafana provisionado (ADR-011). La API debe ser autenticada (Bearer token) en endpoints `/v1/*` y abierta en endpoints health/metrics.

## Health endpoints (públicos)

### `GET /healthz`

- **Auth**: ninguna.
- **Response 200**:
  ```json
  {"status": "ok", "version": "0.1.0", "uptime": 123.45}
  ```

### `GET /readyz`

- **Auth**: ninguna.
- **Response 200** si `mqtt_connected=true` y `config_loaded=true`:
  ```json
  {"status": "ready", "checks": {"mqtt_connected": true, "config_loaded": true}}
  ```
- **Response 503** si no listo:
  ```json
  {"status": "not_ready", "checks": {"mqtt_connected": false, "config_loaded": true}}
  ```

### `GET /metrics`

- **Auth**: ninguna.
- **Content-Type**: `text/plain; version=0.0.4; charset=utf-8` (Prometheus format).

## Control plane (`/v1/control`, autenticados)

### Autenticación

- Header `Authorization: Bearer <BMS_API_TOKEN>`.
- Si `BMS_API_TOKEN` env vacía, auth deshabilitada (solo dev).
- Falla con `401 Unauthorized` si token incorrecto.

### `POST /v1/control/start`

- **Body**:
  ```json
  {
    "config_path": "/app/config/projects/bms_v1_demo.yaml",
    "mode": "live" | "backfill",
    "aulas": 10,
    "faults": ["valve_stuck"]
  }
  ```
- **Validación**:
  - `mode` ∈ `{"live", "backfill"}`.
  - `aulas` ∈ `[1, 70]`.
  - `faults` ⊆ `{"sensor_drift","valve_stuck","fan_failure","refrigerant_low"}`.
- **Response 202 Accepted**:
  ```json
  {"job_id": "abc123def456"}
  ```
- **Response 409 Conflict** si runner ya activo.

### `POST /v1/control/stop?job_id=<id>`

- **Response 200**: `{"stopped": "<job_id>"}`.
- **Response 404** si job_id no existe.

### `GET /v1/control/status?job_id=<id>` (auth opcional)

- **Response 200**:
  ```json
  {
    "job_id": "abc123",
    "phase": "live" | "backfill" | "pending" | "stopped" | "completed" | "error",
    "started_at": "2026-05-09T15:30:00Z",
    "points_emitted": 150420
  }
  ```

## Dataset endpoints (`/v1/datasets`, autenticados)

### `POST /v1/datasets/export`

- **Body**:
  ```json
  {
    "months": 12,
    "format": "line_protocol" | "csv_long",
    "include_faults": true,
    "config_path": "/app/config/projects/bms_v1_caseB_consumption.yaml"
  }
  ```
- **Response 202**:
  ```json
  {"job_id": "exp789", "output_path": "/app/output/ies_simarro_12m.lp"}
  ```

### `GET /v1/datasets/jobs/{job_id}`

- **Response 200**:
  ```json
  {
    "status": "in_progress" | "done" | "error",
    "progress": 0.42,
    "output_path": "/app/output/ies_simarro_12m.lp",
    "size_bytes": 1234567890,
    "sha256": "abc...",
    "started_at": "...",
    "finished_at": "..."
  }
  ```

## Errores estandarizados (problem+json-like)

```json
{
  "error": "validation_failed",
  "message": "Detalle del error en español",
  "trace_id": "00000000abc..."
}
```

Códigos:
- `validation_failed` (400)
- `unauthorized` (401)
- `not_found` (404)
- `conflict` (409)
- `internal_error` (500)

## OpenAPI

- Generado por FastAPI en `/openapi.json`.
- Swagger UI en `/docs` (deshabilitada en producción si `ENVIRONMENT=production`).

## CORS

- Default: `localhost:3001` (Grafana) + `localhost:8120` (self).
- Configurable vía `BMS_CORS_ALLOW_ORIGINS` env.

## UI

- **Grafana** provisionado (ver `05-observability-spec.md`).
- 4 dashboards: overview, iaq, consumption, faults.
- No UI custom v1.

## Acceptance criteria

| ID | Criterio | Validación |
|----|----------|-----------|
| API-01 | `/healthz` y `/metrics` responden sin auth | `curl :8120/healthz` 200 |
| API-02 | `/v1/control/start` requiere Bearer token | Sin token → 401; con token → 202 |
| API-03 | Body inválido devuelve 400 con `validation_failed` | Test integración con `mode:"invalid"` |
| API-04 | Concurrent start cuando hay job activo → 409 | Test integración |
| API-05 | OpenAPI disponible en `/openapi.json` | `curl :8120/openapi.json` 200 |
| API-06 | Dataset export job ID consultable | `GET /v1/datasets/jobs/{id}` 200 |
