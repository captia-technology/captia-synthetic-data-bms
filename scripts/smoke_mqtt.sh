#!/usr/bin/env bash
# =============================================================================
# smoke_mqtt.sh — publica a Mosquitto y comprueba que el broker responde.
# =============================================================================
set -euo pipefail

PORT="${MQTT_PORT_HOST:-1884}"
TOPIC="captia/dev/default/ies_simarro/AULA01/telemetry/co2"
PAYLOAD='{"value": 712.0, "ts_ns": 1715260800000000000}'

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
