# bms-data-generator

Microservicio FastAPI que orquesta el generador hexagonal vendorizado (`synthetic-generator`) más calibración local (`bms_calibration`).

## Endpoints

- `GET /healthz` — health (público).
- `GET /readyz` — readiness (público).
- `GET /metrics` — Prometheus metrics (público).
- `POST /v1/control/start` — arranca generador (requiere `Authorization: Bearer <BMS_API_TOKEN>`).
- `POST /v1/control/stop` — detiene generador.
- `GET /v1/control/status` — estado actual.
- `POST /v1/datasets/export` — exporta dump a archivo.
- `GET /v1/datasets/jobs/{job_id}` — estado de job de export.

Ver `docs/specs/synthetic-bms/06-api-and-ui-spec.md`.

## Configuración

Variables de entorno con prefijo `BMS_`. Ver `.env.example` raíz.

## Ejecución local

```bash
uv run python -m bms_data_generator
```
