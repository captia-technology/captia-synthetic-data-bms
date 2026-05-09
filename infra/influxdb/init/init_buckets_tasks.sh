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

# Look up bucket metadata via REST (avoids 'influx bucket update' CLI quirks
# in v2.7 where neither --org-id nor --name are valid identifiers).
_bucket_lookup() {
    name="$1"
    curl -sS -H "Authorization: Token ${INFLUX_TOKEN}" \
        "${INFLUX_HOST}/api/v2/buckets?org-id=${ORG_ID}&name=${name}" 2>/dev/null \
        | tr -d ' \t\r\n'
}

create_bucket_if_missing() {
    name="$1"
    retention="$2"
    target_seconds=$(_retention_to_seconds "${retention}")
    if echo "${existing_buckets}" | grep -qx "${name}"; then
        body=$(_bucket_lookup "${name}")
        bucket_id=$(echo "${body}" \
            | grep -o "\"id\":\"[^\"]*\",\"orgID\"[^}]*\"name\":\"${name}\"" \
            | grep -o '"id":"[^"]*"' | head -n1 | sed 's/"id":"//; s/"$//')
        actual_seconds=$(echo "${body}" \
            | grep -o "\"name\":\"${name}\"[^}]*\"everySeconds\":[0-9]*" \
            | grep -o '"everySeconds":[0-9]*' | head -n1 | sed 's/"everySeconds"://')
        if [ "${actual_seconds:-0}" = "${target_seconds}" ]; then
            echo "bucket exists: ${name} (retention OK: ${retention})"
        elif [ -n "${bucket_id}" ]; then
            echo "bucket exists: ${name} — updating retention ${actual_seconds:-?}s -> ${retention} (${target_seconds}s)"
            influx bucket update --id "${bucket_id}" --retention "${retention}" \
                || echo "  WARN: could not update retention for ${name}"
        else
            echo "bucket exists: ${name} — could not resolve id (skipping update)"
        fi
    else
        echo "creating bucket: ${name} (${retention})"
        influx bucket create --org-id "${ORG_ID}" --name "${name}" --retention "${retention}"
        existing_buckets="${existing_buckets}
${name}"
    fi
}

# Convert a retention spec like '14d', '30d', '720h', '0' to seconds.
_retention_to_seconds() {
    spec="$1"
    case "${spec}" in
        0|0s|infinite) echo 0 ;;
        *d) echo $(( ${spec%d} * 86400 )) ;;
        *h) echo $(( ${spec%h} * 3600 )) ;;
        *m) echo $(( ${spec%m} * 60 )) ;;
        *s) echo "${spec%s}" ;;
        *) echo "${spec}" ;;
    esac
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

# =============================================================================
# Populate captia_metadata bucket from config/domains/<domain>/variables.yaml
# Closes the gap reported by CENTINELA+ guide (line 549, 268): the rollup
# tasks only emit data for variables present in captia_metadata.
# =============================================================================
populate_metadata() {
    domain_dir="$1"
    [ -d "${domain_dir}" ] || return 0
    domain_id=$(basename "${domain_dir}")
    yaml_file="${domain_dir}/variables.yaml"
    [ -f "${yaml_file}" ] || return 0
    echo "populating captia_metadata from ${yaml_file} (domain=${domain_id})"
    site_id="${CAPTIA_SITE:-ies_simarro}"
    captia_env="${CAPTIA_ENV:-dev}"
    ts_ns=$(date +%s)000000000

    # Idempotencia: borrar todos los registros previos del measurement
    # captia_point_meta (alineado con producción slide 9) para este dominio
    # antes de re-poblar. Mantiene el bucket coherente entre re-runs.
    # Nota: también limpia legacy captia_metadata measurement (pre-T-PV-23).
    for legacy_measurement in captia_point_meta captia_metadata; do
        influx delete \
            --bucket captia_metadata --org-id "${ORG_ID}" \
            --start 1970-01-01T00:00:00Z --stop 2099-12-31T23:59:59Z \
            --predicate "_measurement=\"${legacy_measurement}\" AND domain_id=\"${domain_id}\"" \
            >/dev/null 2>&1 || true
    done
    echo "  - cleared previous records for domain=${domain_id}"

    # YAML parser (sh-portable): emite 1 line-protocol record por variable a
    # measurement captia_point_meta (alineado con docs/influxdb-simarro-buckets.pptx
    # slide 9 y consumido por las Flux tasks tier-1 vía allowlist por metric_kind).
    # Tags: captia_env, domain_id, site_id, asset_type, variable
    # Fields: metric_kind, storage_mode, data_type, unit, point_type, category,
    #         range_min, range_max, vendor_name (si production_name override).
    # Soporta:
    #   - Indent vendor real (6 spaces lista entry, 8 spaces fields).
    #   - range: [a, b] (lista YAML compacta).
    #   - production_name: <prod_name> (override local; alinea con simarro-prod).
    awk -v env="${captia_env}" -v domain="${domain_id}" -v site="${site_id}" -v ts="${ts_ns}" '
        BEGIN {
            asset_type = "classroom"
            name = ""
        }
        # Capture asset_type (e.g., "  classroom:" inside "asset_types:").
        /^  [a-z_][a-z_0-9]*:[[:space:]]*$/ {
            t = $1; gsub(":", "", t); gsub("^ +", "", t); asset_type = t
            next
        }
        # Variable list entry start: "      - name: foo" (6 spaces + dash).
        /^      - name:/ {
            if (name != "") emit();
            name = $3; gsub("\"|'\''", "", name);
            prod_name = ""; data_type = ""; unit = "";
            point_type = ""; metric_kind = ""; category = "";
            storage_mode = ""; rmin = ""; rmax = "";
            next;
        }
        /^        production_name:/ { val = $0; sub(/^        production_name:[[:space:]]*/, "", val); gsub("\"|'\''", "", val); prod_name = val; next }
        /^        data_type:/       { val = $0; sub(/^        data_type:[[:space:]]*/, "", val); data_type = val; next }
        /^        unit:/            { val = $0; sub(/^        unit:[[:space:]]*/, "", val); gsub("\"|'\''", "", val); unit = val; next }
        /^        point_type:/      { val = $0; sub(/^        point_type:[[:space:]]*/, "", val); point_type = val; next }
        /^        metric_kind:/     { val = $0; sub(/^        metric_kind:[[:space:]]*/, "", val); metric_kind = val; next }
        /^        category:/        { val = $0; sub(/^        category:[[:space:]]*/, "", val); category = val; next }
        /^        storage_mode:/    { val = $0; sub(/^        storage_mode:[[:space:]]*/, "", val); storage_mode = val; next }
        /^        range:/ {
            val = $0;
            sub(/^        range:[[:space:]]*\[/, "", val);
            sub(/\][[:space:]]*$/, "", val);
            n = split(val, a, /,[[:space:]]*/);
            if (n >= 2) { rmin = a[1]; rmax = a[2]; }
            next;
        }
        END { if (name != "") emit(); }
        function emit(    emit_name, tags, fields) {
            # Use production_name if defined, else fall back to vendor name.
            emit_name = (prod_name != "") ? prod_name : name;
            # InfluxDB tag values escape spaces and commas.
            gsub(/[, ]/, "_", emit_name);
            # Derive storage_mode from metric_kind if absent (partner spec slide 8).
            if (storage_mode == "") {
                if (metric_kind == "bool_state" || metric_kind == "setpoint_step") {
                    storage_mode = "on_change";
                } else {
                    storage_mode = "continuous";
                }
            }
            tags = "captia_env=" env ",domain_id=" domain ",site_id=" site ",asset_type=" asset_type ",variable=" emit_name;
            # Required fields. Strings double-quoted; numbers raw.
            fields = "metric_kind=\"" metric_kind "\",storage_mode=\"" storage_mode "\""
            if (data_type != "")  fields = fields ",data_type=\"" data_type "\""
            if (unit != "")       fields = fields ",unit=\"" unit "\""
            if (point_type != "") fields = fields ",point_type=\"" point_type "\""
            if (category != "")   fields = fields ",category=\"" category "\""
            if (rmin != "")       fields = fields ",range_min=" rmin
            if (rmax != "")       fields = fields ",range_max=" rmax
            if (prod_name != "" && prod_name != name) fields = fields ",vendor_name=\"" name "\""
            print "captia_point_meta," tags " " fields " " ts
        }
    ' "${yaml_file}" > /tmp/metadata.lp
    lines=$(wc -l < /tmp/metadata.lp 2>/dev/null || echo 0)
    if [ "${lines}" -gt 0 ]; then
        influx write --org-id "${ORG_ID}" --bucket captia_metadata \
            --file /tmp/metadata.lp \
            && echo "  - wrote ${lines} captia_point_meta records"
    else
        echo "  - WARN: no variables parsed from ${yaml_file}"
    fi
}

if [ -d /domains ]; then
    for d in /domains/*/; do
        [ -d "${d}" ] && populate_metadata "${d%/}"
    done
fi

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
