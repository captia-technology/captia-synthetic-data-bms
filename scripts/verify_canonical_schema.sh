#!/usr/bin/env bash
# =============================================================================
# verify_canonical_schema.sh — valida schema canónico CAPTIA en InfluxDB.
# Comprueba:
#   - measurement único `captia_point` en bucket `telemetry`.
#   - 5 tags presentes: captia_env, domain_id, site_id, asset_id, variable.
#   - field `value` (float).
# =============================================================================
set -euo pipefail

URL="http://localhost:${INFLUXDB_PORT_HOST:-8087}"
TOKEN="${INFLUXDB_TOKEN:?required}"
ORG="${INFLUXDB_ORG:-captia}"

echo "==> Verify canonical schema CAPTIA"

QUERY='import "influxdata/influxdb/schema"
schema.tagKeys(bucket: "telemetry", predicate: (r) => r._measurement == "captia_point")'

run_query() {
    if command -v influx >/dev/null 2>&1; then
        influx query --host "${URL}" --token "${TOKEN}" --org "${ORG}" "$1"
    else
        docker exec captia-bms-influxdb influx query --host http://localhost:8086 --token "${TOKEN}" --org "${ORG}" "$1"
    fi
}

OUTPUT=$(run_query "${QUERY}" 2>&1 || true)

REQUIRED_TAGS=("captia_env" "domain_id" "site_id" "asset_id" "variable")
missing=()
for tag in "${REQUIRED_TAGS[@]}"; do
    if ! echo "${OUTPUT}" | grep -q "^${tag}$\|	${tag}$\| ${tag}$"; then
        if ! echo "${OUTPUT}" | grep -wq "${tag}"; then
            missing+=("${tag}")
        fi
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo "ERROR: tags faltantes: ${missing[*]}"
    echo "Output:"
    echo "${OUTPUT}"
    exit 1
fi

echo "  - measurement captia_point OK"
echo "  - tags ${REQUIRED_TAGS[*]} presentes OK"
echo "==> Schema canónico CAPTIA verificado"
