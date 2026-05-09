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

required="telemetry telemetry_1m telemetry_15m telemetry_1h state_events telemetry_events captia_metadata"
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

echo "  - 7 buckets canónicos presentes (telemetry, _1m, _15m, _1h, state_events, telemetry_events, captia_metadata)"

# Bonus: validar que captia_metadata está poblado (gap CENTINELA+ § 549).
# Validar que captia_point_meta está poblado (gap CENTINELA+ § 549).
# Slide 9 simarro-prod: el measurement canónico es 'captia_point_meta'
# dentro del bucket 'captia_metadata'.
md_count=$(curl -fsS -X POST -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/vnd.flux" \
    "${URL}/api/v2/query?org=${ORG}" \
    --data 'from(bucket:"captia_metadata") |> range(start:-1d) |> filter(fn:(r) => r._measurement=="captia_point_meta" and r._field=="metric_kind") |> group() |> count() |> rename(columns:{_value:"n"})' 2>/dev/null \
    | tr -d '\r' \
    | awk -F, 'NF>=6 && $6 ~ /^[0-9]+$/ {print $6; exit}')
if [ -n "${md_count:-}" ] && [ "${md_count}" -ge 21 ]; then
    echo "  - captia_point_meta poblado (${md_count} variables)"
else
    echo "  - WARN: captia_point_meta casi vacío (${md_count:-0} variables; esperadas ≥ 21)"
fi
echo "==> Smoke InfluxDB OK"
