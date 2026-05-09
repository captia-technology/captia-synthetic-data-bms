# Operaciones — Inicialización de `.env`

> **Última verificación:** 2026-05-10
> **Cierra:** H-09 (`docs/audit/AUDIT_REPORT.md`).
> **Source:** [`scripts/init_env.sh`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/scripts/init_env.sh) · [`.env.example`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/.env.example).

## Para qué sirve

Genera el archivo `.env` que el stack necesita. Sustituye los placeholders
`CHANGE_ME_USE_OPENSSL_RAND` de `.env.example` por **secretos aleatorios
locales** generados con `openssl rand`. El archivo `.env` está incluido en
`.gitignore` y nunca debe comprometerse.

## Cuándo se ejecuta

- **Manualmente**: `make init-env` (idempotente — si `.env` existe, no se
  toca).
- **Implícito**: `make demo`, `make quickstart`, `make quickstart-infra`
  invocan `make init-env` antes de cualquier otro paso, por lo que un
  alumno de FP no necesita pensar en él.
- **Recreación forzada**: `make init-env-force` o
  `bash scripts/init_env.sh --force`.

## Qué genera

Tres secretos, todos vía `openssl rand`:

| Variable | Longitud | Uso |
|---|---|---|
| `INFLUXDB_TOKEN` | 64 hex (32 bytes) | Token admin InfluxDB; lo usa Telegraf, init script, generador, scripts smoke |
| `INFLUXDB_ADMIN_PASSWORD` | 32 hex (16 bytes) | Contraseña UI InfluxDB (admin) |
| `BMS_API_TOKEN` | 64 hex (32 bytes) | Bearer token para `/v1/control` y `/v1/datasets` |

El resto de variables del `.env.example` se copian literalmente (puertos,
nombres de host, URLs internas, configuración del generator).

## Verificación post-init

```bash
make init-env       # genera .env si no existe
make preflight      # verifica docker, ports, .env presente
make up             # arranca el stack con secretos del .env
```

`scripts/preflight.sh` falla con mensaje claro si:

- Docker daemon no responde.
- Puertos en `.env` ya están ocupados (`MQTT_PORT_HOST`,
  `INFLUXDB_PORT_HOST`, `GRAFANA_PORT_HOST`, `PROMETHEUS_PORT_HOST`,
  `LOKI_PORT_HOST`, `BMS_GENERATOR_PORT_HOST`).
- `.env` falta variables requeridas (`INFLUXDB_TOKEN`,
  `INFLUXDB_ADMIN_PASSWORD`, `BMS_API_TOKEN`).

## Anti-patrón: secretos en código

> **No** edites manualmente el `.env` para hardcodear secretos en
> commits, dumps de logs, o screenshots. Si necesitas un valor estable
> entre máquinas, ponlo en un secret manager (Doppler, AWS Secrets, etc.)
> y exporta `INFLUXDB_TOKEN` en el shell antes de `make up` — el Makefile
> usa la variable del entorno si ya está definida.

## Recreación cuando hay que rotar secretos

```bash
make down            # parar stack
make init-env-force  # nuevo .env con tokens distintos
make clean           # destruir volúmenes (importante: InfluxDB persiste tokens)
make up              # arrancar de cero
```

Sin `make clean`, los volúmenes de InfluxDB conservan el token anterior y
el nuevo `.env` no concuerda con el datastore.

## Cómo se invoca desde CI

`.github/workflows/ci.yml` job `e2e-stack` ejecuta
`bash scripts/init_env.sh` antes de `make demo`. Cada run de CI obtiene
secretos aleatorios efímeros que viven sólo dentro del runner. No se
suben artifacts con `.env` sin redactar.

## Cómo lo usa el agente claude/cursor

`.claude/settings.local.json` permite al agente leer `.env.example` (es
público) pero no `.env` (secretos). Si Claude Code necesita mostrar
configuración del `.env`, lo hará pidiendo al usuario que comparta el
valor manualmente o solicitando que ejecute `make init-env`.

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---|---|---|
| `openssl: command not found` | macOS/Windows sin OpenSSL en PATH | Instalar Git Bash en Windows o `brew install openssl@3` en macOS |
| `make demo` falla con 401 contra InfluxDB | `.env` regenerado pero los volúmenes persisten el token antiguo | `make clean` + `make demo` |
| `make demo` falla al inicio con "BMS_API_TOKEN required" | `.env` corrupto o `init-env` falló | `make init-env-force` |
| `git status` muestra `.env` como modificado | `.env` no está en `.gitignore` | Ya está; verificar `git check-ignore -v .env` |
