#!/usr/bin/env bash
# =============================================================================
# smoke_influx.sh — verifica InfluxDB up + bucket telemetry presente.
# =============================================================================
set -euo pipefail

PORT="${INFLUXDB_PORT_HOST:-8087}"
URL="http://localhost:${PORT}"

echo "==> Smoke InfluxDB (${URL})"

# /health endpoint
curl -fsS "${URL}/health" | grep -q '"status":"pass"' && echo "  - /health OK" || {
    echo "ERROR: InfluxDB no healthy"
    exit 1
}

# Bucket list
TOKEN="${INFLUXDB_TOKEN:?required}"
ORG="${INFLUXDB_ORG:-captia}"

if command -v influx >/dev/null 2>&1; then
    influx bucket list --host "${URL}" --token "${TOKEN}" --org "${ORG}" | grep -q "^[a-f0-9]\+\s\+telemetry\s" \
        && echo "  - bucket telemetry OK" \
        || { echo "ERROR: bucket telemetry no encontrado"; exit 1; }
else
    docker exec captia-bms-influxdb influx bucket list --host http://localhost:8086 --token "${TOKEN}" --org "${ORG}" \
        | grep -q "^[a-f0-9]\+\s\+telemetry\s" \
        && echo "  - bucket telemetry OK (vía container)" \
        || { echo "ERROR: bucket telemetry no encontrado"; exit 1; }
fi

echo "==> Smoke InfluxDB OK"
