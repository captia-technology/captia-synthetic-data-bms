#!/usr/bin/env bash
# =============================================================================
# wait_healthy.sh — espera hasta que todos los servicios persistentes estén
# en estado `healthy` (max 120 s).
# =============================================================================
set -euo pipefail

DEADLINE=$(($(date +%s) + 120))
SERVICES=(captia-bms-mosquitto captia-bms-influxdb captia-bms-redis captia-bms-telegraf captia-bms-grafana captia-bms-prometheus captia-bms-loki captia-bms-generator)

while [ $(date +%s) -lt ${DEADLINE} ]; do
    all_healthy=true
    for svc in "${SERVICES[@]}"; do
        status=$(docker inspect --format='{{.State.Health.Status}}' "${svc}" 2>/dev/null || echo "missing")
        if [ "${status}" != "healthy" ]; then
            all_healthy=false
        fi
    done
    if [ "${all_healthy}" = "true" ]; then
        echo "==> All services healthy"
        exit 0
    fi
    sleep 5
done

echo "ERROR: timeout esperando healthchecks"
docker compose ps
exit 1
