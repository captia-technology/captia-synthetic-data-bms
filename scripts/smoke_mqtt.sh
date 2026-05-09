#!/usr/bin/env bash
# =============================================================================
# smoke_mqtt.sh — publica a Mosquitto y comprueba que el broker responde.
# =============================================================================
set -euo pipefail

PORT="${MQTT_PORT_HOST:-1884}"
ENV_NAME="${CAPTIA_ENV:-dev}"
DOMAIN="${BMS_DOMAIN_ID:-bms_classrooms}"
SITE="${CAPTIA_SITE:-ies_simarro}"
TOPIC="captia/${ENV_NAME}/${DOMAIN}/${SITE}/AULA01/telemetry/co2"
# Use current epoch ns so the point falls inside the bucket retention window.
TS_NS="$(date +%s)000000000"
PAYLOAD="{\"value\":712.0,\"ts_ns\":${TS_NS}}"

echo "==> Smoke MQTT (puerto ${PORT})"

# Publicar (asume mosquitto-clients en host o en captia-bms-mosquitto container)
if command -v mosquitto_pub >/dev/null 2>&1; then
    mosquitto_pub -h localhost -p "${PORT}" -t "${TOPIC}" -m "${PAYLOAD}" -q 1
    echo "  - publish OK (host client)"
else
    docker exec captia-bms-mosquitto mosquitto_pub \
        -h localhost -p 1883 -t "${TOPIC}" -m "${PAYLOAD}" -q 1
    echo "  - publish OK (container client)"
fi

echo "==> Smoke MQTT OK"
