#!/usr/bin/env bash
# =============================================================================
# smoke_grafana.sh — verifica Grafana healthz + datasources provisionados.
# =============================================================================
set -euo pipefail
# shellcheck disable=SC1091
source "$(dirname "$0")/_load_env.sh"

PORT="${GRAFANA_PORT_HOST:-3001}"
URL="http://localhost:${PORT}"
USER="${GRAFANA_ADMIN_USER:-admin}"
PASS="${GRAFANA_ADMIN_PASSWORD:-admin}"

echo "==> Smoke Grafana (${URL})"

# Health
curl -fsS "${URL}/api/health" | grep -q '"database": "ok"' && echo "  - /api/health OK" || {
    echo "ERROR: Grafana no healthy"
    exit 1
}

# Datasources
DS=$(curl -fsS -u "${USER}:${PASS}" "${URL}/api/datasources" | grep -oE '"name":"[^"]+"' | wc -l)
if [ "${DS}" -ge 3 ]; then
    echo "  - datasources provisionados (${DS}) OK"
else
    echo "ERROR: solo ${DS} datasources provisionados, se esperaban ≥ 3"
    exit 1
fi

echo "==> Smoke Grafana OK"
