#!/bin/sh
# =============================================================================
# Init script — InfluxDB buckets + Flux tasks (one-shot)
# =============================================================================
# Crea los 6 buckets canónicos CAPTIA si no existen y aplica las 5 tareas Flux
# de downsampling. Idempotente.
#
# Ejecutado por compose/data-plane-init.yaml (servicio influx-init,
# restart: "no").
# =============================================================================
set -eu

export INFLUX_HOST="${INFLUXDB_URL:-http://influxdb:8086}"
export INFLUX_TOKEN="${INFLUXDB_TOKEN}"
export INFLUX_ORG="${INFLUXDB_ORG:-captia}"

# Wait for the InfluxDB API to become reachable AND authenticate the admin
# token. The healthcheck on the service can flip to "healthy" before the
# token database is fully primed, so we retry up to 30s before giving up.
ORG_ID=""
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    response=$(curl -sS -H "Authorization: Token ${INFLUX_TOKEN}" \
        "${INFLUX_HOST}/api/v2/orgs?org=${INFLUX_ORG}" 2>&1 || true)
    ORG_ID=$(echo "${response}" | tr -d ' ' | grep -o '"id":"[^"]*"' | head -n1 | sed 's/"id":"//; s/"$//')
    if [ -n "${ORG_ID}" ]; then
        break
    fi
    echo "(attempt ${attempt}) org lookup not ready yet — response: ${response}"
    sleep 2
done
if [ -z "${ORG_ID}" ]; then
    echo "ERROR: could not resolve org id for org=${INFLUX_ORG}"
    exit 1
fi
echo "org=${INFLUX_ORG} id=${ORG_ID}"

# From here on we drive the CLI by --org-id only. INFLUX_ORG would otherwise
# clash with --org-id ("ambiguous org" error in CLI 2.7).
unset INFLUX_ORG

existing_buckets=""

refresh_bucket_cache() {
    existing_buckets=$(influx bucket list --org-id "${ORG_ID}" 2>/dev/null | awk 'NR>1 {print $2}')
}

create_bucket_if_missing() {
    name="$1"
    retention="$2"
    if echo "${existing_buckets}" | grep -qx "${name}"; then
        echo "bucket exists: ${name}"
    else
        echo "creating bucket: ${name} (${retention})"
        influx bucket create --org-id "${ORG_ID}" --name "${name}" --retention "${retention}"
        existing_buckets="${existing_buckets}
${name}"
    fi
}

refresh_bucket_cache

create_bucket_if_missing "telemetry" "14d"
create_bucket_if_missing "telemetry_1m" "30d"
create_bucket_if_missing "telemetry_15m" "90d"
create_bucket_if_missing "telemetry_1h" "365d"
create_bucket_if_missing "state_events" "90d"
# T-PV-18 (cierra L-PV-18): 7º bucket operativo alineado con producción simarro-prod.
# Almacena eventos de plataforma (cmd_authorized, cmd_rejected, sniper_error)
# vía 2º mqtt_consumer + output #3 en infra/telegraf/telegraf.conf.
# Source of truth: docs/influxdb-simarro-buckets.pptx slide 8.
create_bucket_if_missing "telemetry_events" "90d"
create_bucket_if_missing "captia_metadata" "0"

existing_tasks=$(influx task list --org-id "${ORG_ID}" 2>/dev/null | awk 'NR>1 {print $4}')
for task_file in /tasks/*.flux; do
    if [ -f "${task_file}" ]; then
        name=$(basename "${task_file}" .flux)
        if echo "${existing_tasks}" | grep -qx "${name}"; then
            echo "task exists: ${name}"
        else
            echo "applying task: ${task_file}"
            influx task create --org-id "${ORG_ID}" --file "${task_file}" \
                || echo "(task create failed; continuing)"
        fi
    fi
done

echo "init complete"
