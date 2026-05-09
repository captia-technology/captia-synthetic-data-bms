# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ |
| < 0.1   | ❌ |

## Reporting a vulnerability

Please **do not open a public GitHub issue** for security problems.

Send an email to **jaime.sendra@captiatechnology.com** with:

- Description of the vulnerability and possible impact.
- Steps to reproduce.
- Affected version, commit or container tag.
- Your contact for follow-up.

We aim to:

1. Acknowledge receipt within **3 business days**.
2. Provide an initial assessment within **7 business days**.
3. Coordinate disclosure timing with the reporter.

PGP / encrypted email is available on request.

## Default credentials are for development only

This repository ships with insecure defaults to make local development
trivial. **Do not deploy as-is to any environment exposed to the internet.**

| Component | Dev default | Production action |
|-----------|-------------|-------------------|
| Mosquitto | `allow_anonymous true`, no users | Enable `password_file` + `acl_file`, set `allow_anonymous false`. |
| Grafana   | `admin / admin` | Set `GRAFANA_ADMIN_PASSWORD` to a strong secret; enable SSO/RBAC. |
| InfluxDB  | Token in `.env` | Inject token via secret manager; rotate periodically. |
| BMS API   | `BMS_API_TOKEN` empty disables auth | Always set `BMS_API_TOKEN` to a 32-byte hex secret. |
| CORS      | Allows `localhost:3001` and `localhost:8120` | Restrict to your real frontend origin. |
| Compose   | Binds host ports to `0.0.0.0` | Bind to `127.0.0.1` or place behind a reverse proxy with TLS. |
| Telegraf  | Anonymous MQTT consumer | Provide `MQTT_USER` / `MQTT_PASSWORD` and TLS. |

The required env vars use `${VAR:?required}` in compose files so the stack
will refuse to start without them.

## Threat model (summary)

- **Trust boundary**: only the `bms-data-generator` HTTP API and Grafana
  are intended to be reachable from outside the Docker network. All other
  services (Mosquitto, InfluxDB, Redis, Prometheus, Loki) should stay
  inside the `captia-network` overlay.
- **Authentication**: Bearer token on `/v1/*`. Tokens are compared with
  constant-prefix equality; consider replacing with `hmac.compare_digest`
  for stronger guarantees in production deployments.
- **Authorization**: there are no roles in v0.1.x; anyone with the
  `BMS_API_TOKEN` can trigger generation and dump exports. Plan for RBAC
  in future versions if multi-tenant.
- **Data sensitivity**: all data is **synthetic** by design. There is no
  PII or real student information in the generated stream.
- **Supply chain**: vendor sources are committed under `vendor/`.
  Container images are pinned to specific versions. `uv.lock` pins
  Python deps. Dependabot is enabled (`.github/dependabot.yml`).

## Hardening checklist before production

- [ ] Set strong values for `BMS_API_TOKEN`, `INFLUXDB_TOKEN`,
      `INFLUXDB_ADMIN_PASSWORD`, `GRAFANA_ADMIN_PASSWORD`.
- [ ] Disable Mosquitto anonymous access; enable TLS on port 8883.
- [ ] Restrict CORS via `BMS_CORS_ALLOW_ORIGINS`.
- [ ] Disable FastAPI `/docs` and `/redoc` (set `ENVIRONMENT=production`).
- [ ] Pin all images to digests, not tags, before release.
- [ ] Rotate Telegraf statefile volume permissions; back up periodically.
- [ ] Run `pip-audit` / `osv-scanner` against `uv.lock`.
- [ ] Enable HTTPS in front of Grafana and the BMS API.
