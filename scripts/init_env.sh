#!/usr/bin/env bash
# =============================================================================
# init_env.sh — generate a working .env from .env.example.
# Replaces every CHANGE_ME_USE_OPENSSL_RAND placeholder with a fresh random
# secret. Idempotent: if .env already exists, do nothing unless --force.
# =============================================================================
set -euo pipefail

FORCE=0
if [ "${1:-}" = "--force" ]; then
    FORCE=1
fi

ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

if [ ! -f "${EXAMPLE_FILE}" ]; then
    echo "ERROR: ${EXAMPLE_FILE} not found. Run from repo root."
    exit 1
fi

if [ -f "${ENV_FILE}" ] && [ "${FORCE}" -eq 0 ]; then
    echo "  - .env already exists (skipping). Use --force to recreate."
    exit 0
fi

if ! command -v openssl >/dev/null 2>&1; then
    echo "ERROR: openssl is required to generate secrets."
    exit 1
fi

INFLUXDB_TOKEN_VAL="$(openssl rand -hex 32)"
INFLUXDB_ADMIN_PASSWORD_VAL="$(openssl rand -hex 16)"
BMS_API_TOKEN_VAL="$(openssl rand -hex 32)"

# Pure-bash replacement to avoid sed quoting differences across platforms.
generated="$(awk -v t="${INFLUXDB_TOKEN_VAL}" \
                 -v p="${INFLUXDB_ADMIN_PASSWORD_VAL}" \
                 -v a="${BMS_API_TOKEN_VAL}" '
{
    if ($0 ~ /^INFLUXDB_TOKEN=/) print "INFLUXDB_TOKEN=" t;
    else if ($0 ~ /^INFLUXDB_ADMIN_PASSWORD=/) print "INFLUXDB_ADMIN_PASSWORD=" p;
    else if ($0 ~ /^BMS_API_TOKEN=/) print "BMS_API_TOKEN=" a;
    else print $0;
}' "${EXAMPLE_FILE}")"

printf "%s\n" "${generated}" > "${ENV_FILE}"

echo "==> .env created with fresh random secrets (kept locally only)."
echo "    INFLUXDB_TOKEN          = ${INFLUXDB_TOKEN_VAL:0:8}…"
echo "    INFLUXDB_ADMIN_PASSWORD = ${INFLUXDB_ADMIN_PASSWORD_VAL:0:6}…"
echo "    BMS_API_TOKEN           = ${BMS_API_TOKEN_VAL:0:8}…"
