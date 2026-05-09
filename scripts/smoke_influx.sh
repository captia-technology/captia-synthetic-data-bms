#!/usr/bin/env bash
# =============================================================================
# smoke_influx.sh — verifica InfluxDB up + bucket telemetry presente.
# =============================================================================
set -euo pipefail
# shellcheck disable=SC1091
source "$(dirname "$0")/_load_env.sh"

PORT="${INFLUXDB_PORT_HOST:-8087}"
URL="http://localhost:${PORT}"
TOKEN="${INFLUXDB_TOKEN:?required}"
ORG="${INFLUXDB_ORG:-captia}"

echo "==> Smoke InfluxDB (${URL})"

# /health endpoint
if ! curl -fsS "${URL}/health" | grep -q '"status":"pass"'; then
    echo "ERROR: InfluxDB no healthy"
    exit 1
fi
echo "  - /health OK"

# Bucket list via REST API (avoids influx CLI version-specific flags).
buckets=$(curl -fsS -H "Authorization: Token ${TOKEN}" \
    "${URL}/api/v2/buckets?org=${ORG}&limit=100" 2>/dev/null \
    | tr -d ' \t\r\n' \
    | grep -oE '"name":"[^"]+"' | sed 's/"name":"//; s/"$//' || true)

if [ -z "${buckets}" ]; then
    echo "ERROR: no buckets visibles (token o org incorrectos)"
    exit 1
fi

required="telemetry telemetry_1m telemetry_15m telemetry_1h state_events captia_metadata"
missing=""
for b in ${required}; do
    if ! echo "${buckets}" | grep -qx "${b}"; then
        missing="${missing} ${b}"
    fi
done

if [ -n "${missing}" ]; then
    echo "ERROR: buckets faltantes:${missing}"
    echo "(buckets actuales: $(echo "${buckets}" | tr '\n' ' '))"
    exit 1
fi

echo "  - 6 buckets canónicos presentes (telemetry, _1m, _15m, _1h, state_events, captia_metadata)"
echo "==> Smoke InfluxDB OK"
