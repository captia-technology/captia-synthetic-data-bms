#!/bin/sh
set -e

URL="${INFLUX_HOST:-http://influxdb:8086}"
TOKEN="${INFLUX_TOKEN:-}"
ORG="${INFLUX_ORG:-captia}"
ENV="${CAPTIA_ENV:-dev}"
DOMAIN="${BMS_DOMAIN_ID:-bms_classrooms}"
DOMAINS_DIR="${DOMAINS_DIR:-/app/domains}"
N_AULAS="${BMS_N_AULAS:-10}"
# Default behavior on every deploy: --force (purge + rewrite from current YAML).
# This guarantees the catalog reflects the deployed config exactly.
# Override via BOOTSTRAP_MODE env: skip-if-exists, force, purge-old.
MODE="${BOOTSTRAP_MODE:-force}"

echo "metadata-bootstrap:"
echo "  url=$URL  org=$ORG  env=$ENV  domain=$DOMAIN  n_aulas=$N_AULAS  mode=$MODE"
echo "  domains_dir=$DOMAINS_DIR"

# Give InfluxDB a head-start to settle after influx-init (avoid race in deploy).
sleep 3

exec python /app/bootstrap.py \
  --url "$URL" \
  --token "$TOKEN" \
  --org "$ORG" \
  --env "$ENV" \
  --domain "$DOMAIN" \
  --domains-dir "$DOMAINS_DIR" \
  --n-aulas "$N_AULAS" \
  --"$MODE"
