#!/usr/bin/env bash
# =============================================================================
# export_dump.sh — invoca POST /v1/datasets/export con el caso indicado.
# Uso: ./export_dump.sh {caseB|caseC|caseD}
# =============================================================================
set -euo pipefail
# shellcheck disable=SC1091
source "$(dirname "$0")/_load_env.sh"

CASE="${1:-caseB}"
PORT="${BMS_GENERATOR_PORT_HOST:-8120}"
TOKEN="${BMS_API_TOKEN:?required}"

case "${CASE}" in
    caseB)
        BODY='{"months":12,"format":"line_protocol","include_faults":false,"config_path":"/app/config/projects/bms_v1_caseB_consumption.yaml"}'
        ;;
    caseC)
        BODY='{"months":6,"format":"line_protocol","include_faults":true,"config_path":"/app/config/projects/bms_v1_caseC_faults.yaml"}'
        ;;
    caseD)
        BODY='{"months":3,"format":"line_protocol","include_faults":false,"config_path":"/app/config/projects/bms_v1_caseD_iaq.yaml"}'
        ;;
    *)
        echo "ERROR: caso desconocido: ${CASE}"
        echo "Uso: $0 {caseB|caseC|caseD}"
        exit 1
        ;;
esac

echo "==> Trigger dump export (${CASE})"
RESPONSE=$(curl -fsS -X POST \
    "http://localhost:${PORT}/v1/datasets/export" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "${BODY}")

echo "${RESPONSE}"

JOB_ID=$(echo "${RESPONSE}" | grep -oE '"job_id":"[^"]+"' | head -n1 | cut -d'"' -f4)
echo
echo "Track con: curl http://localhost:${PORT}/v1/datasets/jobs/${JOB_ID} -H 'Authorization: Bearer ${TOKEN}'"
