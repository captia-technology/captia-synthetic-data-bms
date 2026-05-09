#!/usr/bin/env bash
# =============================================================================
# preflight.sh — verifica prerequisitos antes de levantar el stack.
# =============================================================================
set -euo pipefail

echo "==> Preflight CAPTIA-SYNTHETIC-DATA-BMS"

# Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker no está instalado o no en PATH"
    exit 1
fi
docker info >/dev/null 2>&1 || { echo "ERROR: docker daemon no accesible"; exit 1; }
echo "  - docker OK"

# Compose v2
if ! docker compose version >/dev/null 2>&1; then
    echo "ERROR: docker compose v2 no disponible"
    exit 1
fi
echo "  - docker compose v2 OK"

# .env
if [ ! -f .env ]; then
    echo "AVISO: .env no existe. Copia .env.example a .env y rellena valores reales."
    echo "       cp .env.example .env"
fi

# Variables críticas
missing=()
for var in INFLUXDB_TOKEN INFLUXDB_ADMIN_PASSWORD BMS_API_TOKEN; do
    if [ -f .env ]; then
        val=$(grep -E "^${var}=" .env 2>/dev/null | cut -d= -f2- || true)
        if [ -z "${val:-}" ] || [ "${val}" = "CHANGE_ME_USE_OPENSSL_RAND" ]; then
            missing+=("${var}")
        fi
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo "AVISO: variables sin valor real en .env: ${missing[*]}"
    echo "       Genera con: openssl rand -hex 32"
fi

# Puertos host
for port in "${MQTT_PORT_HOST:-1884}" "${INFLUXDB_PORT_HOST:-8087}" "${GRAFANA_PORT_HOST:-3001}" "${BMS_GENERATOR_PORT_HOST:-8120}" "${PROMETHEUS_PORT_HOST:-9090}" "${LOKI_PORT_HOST:-3100}"; do
    if command -v lsof >/dev/null 2>&1 && lsof -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "AVISO: puerto ${port} ya en uso"
    fi
done

echo "==> Preflight OK"
