#!/bin/sh
# =============================================================================
# Grafana demo publisher — emite mensajes MQTT continuos para llenar dashboards.
#
# Uso:
#   bash scripts/grafana_demo_publisher.sh [duración_segundos]
#
# Default: 600s (10 min). Lanzar en otra terminal o como background con `&`.
# Publica 14 variables × 5 aulas cada 5s = 84 msg/sample, ~1000 msg/min.
# =============================================================================
set -eu

DURATION="${1:-600}"
END=$(($(date +%s) + DURATION))
echo "Publishing to MQTT (Mosquitto:1884) for ${DURATION}s ... Ctrl+C to stop."

docker exec captia-bms-mosquitto sh -c "
end=$END
while [ \$(date +%s) -lt \$end ]; do
  TS=\$(date +%s%N)
  for aula in AULA01 AULA02 AULA03 AULA04 AULA05; do
    for v_val in \
      'temperature_01:'\$(awk 'BEGIN { srand(); print 19 + rand() * 6 }') \
      'co2:'\$(awk 'BEGIN { srand(); print 450 + rand() * 800 }') \
      'relative-humidity:'\$(awk 'BEGIN { srand(); print 40 + rand() * 30 }') \
      'iaq-index:'\$(awk 'BEGIN { srand(); print 30 + rand() * 200 }') \
      'people-count:'\$(awk 'BEGIN { srand(); print int(rand() * 25) }') \
      'luminosity:'\$(awk 'BEGIN { srand(); print rand() * 1500 }') \
      'avg-sound-level:'\$(awk 'BEGIN { srand(); print 35 + rand() * 35 }') \
      'power_01:'\$(awk 'BEGIN { srand(); print 100 + rand() * 800 }') \
      'temperature-outdoor:'\$(awk 'BEGIN { srand(); print 12 + rand() * 18 }') \
      'daylight-lux:'\$(awk 'BEGIN { srand(); print rand() * 700 }') \
      'occupancy:'\$(awk 'BEGIN { srand(); print int(rand() * 2) }'); do
      v=\$(echo \"\$v_val\" | cut -d: -f1)
      val=\$(echo \"\$v_val\" | cut -d: -f2)
      mosquitto_pub -h localhost -p 1883 -t \"captia/dev/bms_classrooms/ies_simarro/\$aula/telemetry/\$v\" -m \"{\\\"value\\\": \$val, \\\"ts_ns\\\": \$TS}\"
    done
    for v in ac_state fan_speed_01_state light_01_state; do
      val=\$(awk 'BEGIN { srand(); print int(rand() * 2) }')
      mosquitto_pub -h localhost -p 1883 -t \"captia/dev/bms_classrooms/ies_simarro/\$aula/telemetry/\$v\" -m \"{\\\"value\\\": \$val, \\\"ts_ns\\\": \$TS}\"
    done
  done
  sleep 5
done
echo 'Publisher finished.'
"
