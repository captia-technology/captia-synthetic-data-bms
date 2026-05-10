#!/usr/bin/env bash
# =============================================================================
# Grafana demo publisher — emite mensajes MQTT continuos con production names.
#
# Uso: bash scripts/grafana_demo_publisher.sh [duración_segundos]
# Default: 600s (10 min). Ctrl+C para detener.
#
# Bugfix: Alpine sh date +%s%N solo da segundos. Generamos ns manual desde host.
# =============================================================================
set -eu

DURATION="${1:-600}"
END=$(($(date +%s) + DURATION))
echo "Publishing to MQTT (Mosquitto:1884) for ${DURATION}s ... Ctrl+C to stop."
echo "Variables emitidas: 14 (production names)"

while [ "$(date +%s)" -lt "$END" ]; do
  # Nanos calculados desde host bash (que SÍ soporta %N)
  TS_NS=$(date +%s%N)
  for aula in AULA01 AULA02 AULA03 AULA04 AULA05; do
    for pair in \
      "temperature_01:$(awk 'BEGIN{srand(); print 19 + rand() * 6}')" \
      "co2:$(awk 'BEGIN{srand(); print 450 + rand() * 800}')" \
      "relative-humidity:$(awk 'BEGIN{srand(); print 40 + rand() * 30}')" \
      "iaq-index:$(awk 'BEGIN{srand(); print 30 + rand() * 200}')" \
      "people-count:$(awk 'BEGIN{srand(); print int(rand() * 25)}')" \
      "luminosity:$(awk 'BEGIN{srand(); print rand() * 1500}')" \
      "avg-sound-level:$(awk 'BEGIN{srand(); print 35 + rand() * 35}')" \
      "power_01:$(awk 'BEGIN{srand(); print 100 + rand() * 800}')" \
      "temperature-outdoor:$(awk 'BEGIN{srand(); print 12 + rand() * 18}')" \
      "daylight-lux:$(awk 'BEGIN{srand(); print rand() * 700}')" \
      "occupancy:$(awk 'BEGIN{srand(); print int(rand() * 2)}')" ; do
      v="${pair%%:*}"
      val="${pair#*:}"
      docker exec captia-bms-mosquitto mosquitto_pub -h localhost -p 1883 \
        -t "captia/dev/bms_classrooms/ies_simarro/$aula/telemetry/$v" \
        -m "{\"value\": $val, \"ts_ns\": $TS_NS}"
    done
    for v in ac_state fan_speed_01_state light_01_state; do
      val=$(awk 'BEGIN{srand(); print int(rand() * 2)}')
      docker exec captia-bms-mosquitto mosquitto_pub -h localhost -p 1883 \
        -t "captia/dev/bms_classrooms/ies_simarro/$aula/telemetry/$v" \
        -m "{\"value\": $val, \"ts_ns\": $TS_NS}"
    done
  done
  sleep 5
done
echo "Publisher finished."
