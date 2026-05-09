#!/bin/sh
# =============================================================================
# Init script — InfluxDB buckets + Flux tasks (one-shot)
# =============================================================================
# Crea los 6 buckets canónicos CAPTIA si no existen y aplica las 5 tareas Flux
# de downsampling.
#
# Ejecutado por compose/data-plane-init.yaml (servicio influx-init,
# restart: "no").
# =============================================================================
set -eu

INFLUX="influx --host ${INFLUXDB_URL:-http://influxdb:8086} --token ${INFLUXDB_TOKEN} --org ${INFLUXDB_ORG:-captia}"

create_bucket_if_missing() {
    name="$1"
    retention="$2"
    if ! $INFLUX bucket list 2>/dev/null | awk '{print $2}' | grep -qx "${name}"; then
        echo "creating bucket: ${name} (${retention})"
        $INFLUX bucket create --name "${name}" --retention "${retention}"
    else
        echo "bucket exists: ${name}"
    fi
}

create_bucket_if_missing "telemetry" "14d"
create_bucket_if_missing "telemetry_1m" "30d"
create_bucket_if_missing "telemetry_15m" "90d"
create_bucket_if_missing "telemetry_1h" "365d"
create_bucket_if_missing "state_events" "90d"
create_bucket_if_missing "captia_metadata" "0"

for task_file in /tasks/*.flux; do
    if [ -f "${task_file}" ]; then
        echo "applying task: ${task_file}"
        $INFLUX task create --file "${task_file}" 2>&1 || echo "(task already exists or error, continuing)"
    fi
done

echo "init complete"
