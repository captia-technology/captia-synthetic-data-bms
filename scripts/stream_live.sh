#!/usr/bin/env bash
# =============================================================================
# stream_live.sh — Mantiene el bms-data-generator vivo en modo live (#27).
#
# Uso:
#   bash scripts/stream_live.sh                       # config demo
#   CONFIG=config/projects/bms_v1_caseC_faults.yaml bash scripts/stream_live.sh
#
# Variables (todas con defaults):
#   BMS_GENERATOR_URL — default http://localhost:8120
#   BMS_API_TOKEN     — leído de .env
#   CONFIG            — default /app/config/projects/bms_v1_demo.yaml
#   AULAS             — default 10
#   FAULTS            — default "" (lista CSV de tipos de fallo)
#   POLL_INTERVAL_S   — default 30 (segundos entre comprobaciones)
#
# Comportamiento:
#   1. Carga .env si existe.
#   2. Bucle: si /v1/control/status reporta phase != "running", invoca
#      /v1/control/start con la config dada.
#   3. Sale al recibir SIGINT/SIGTERM con `make down` opcional (no detiene
#      el job — el caller controla eso).
#
# No corre como demonio: usar `make stream` o `nohup bash scripts/stream_live.sh &`.
# =============================================================================

set -euo pipefail

# Cargar .env si existe.
if [[ -f .env ]]; then
    # shellcheck disable=SC1091
    source <(grep -E "^[A-Z_]+=.*$" .env | sed 's/^/export /')
fi

URL="${BMS_GENERATOR_URL:-http://localhost:8120}"
TOKEN="${BMS_API_TOKEN:-}"
CONFIG="${CONFIG:-/app/config/projects/bms_v1_demo.yaml}"
AULAS="${AULAS:-10}"
FAULTS="${FAULTS:-}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-30}"

if [[ -z "$TOKEN" ]]; then
    echo "ERROR: BMS_API_TOKEN no definido (¿falta .env?)" >&2
    exit 1
fi

faults_json="[]"
if [[ -n "$FAULTS" ]]; then
    faults_json=$(echo "$FAULTS" | tr ',' '\n' | awk '{printf "\"%s\",", $0}' | sed 's/,$//')
    faults_json="[$faults_json]"
fi

payload=$(cat <<EOF
{"config_path": "$CONFIG", "mode": "live", "aulas": $AULAS, "faults": $faults_json}
EOF
)

start_job() {
    echo "[stream] $(date -Iseconds) starting live job (config=$CONFIG, aulas=$AULAS, faults=$FAULTS)"
    response=$(curl -fsS -X POST "$URL/v1/control/start" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$payload" || true)
    if [[ -z "$response" ]]; then
        echo "[stream] ERROR: /v1/control/start no devolvió respuesta" >&2
        return 1
    fi
    job_id=$(echo "$response" | grep -oE '"job_id":\s*"[^"]+"' | head -1 | cut -d'"' -f4)
    echo "[stream] job_id=$job_id"
}

current_phase() {
    curl -fsS "$URL/v1/control/status" 2>/dev/null \
        | grep -oE '"phase":\s*"[^"]+"' \
        | head -1 \
        | cut -d'"' -f4 \
        || echo "unknown"
}

trap 'echo "[stream] received signal, exiting (job sigue vivo en el servidor)"; exit 0' INT TERM

echo "[stream] CAPTIA BMS live keep-alive — POLL_INTERVAL_S=$POLL_INTERVAL_S"
while true; do
    phase=$(current_phase)
    case "$phase" in
        running|live)
            : # OK, sigue vivo
            ;;
        *)
            echo "[stream] $(date -Iseconds) phase=$phase (no running) → reiniciando job"
            if ! start_job; then
                echo "[stream] start failed; backoff 60s"
                sleep 60
                continue
            fi
            ;;
    esac
    sleep "$POLL_INTERVAL_S"
done
