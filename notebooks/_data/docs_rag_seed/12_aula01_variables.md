# Variables de AULA01 (IES Simarro)

AULA01 es el aula instrumentada de referencia para CENTINELA+. El gateway
BMS publica las siguientes variables:

| Variable | Unidad | Tipo | Bucket destino |
|---|---|---|---|
| `temperature_01` | °C | analog_gauge | telemetry |
| `relative_humidity_01` | %RH | analog_gauge | telemetry |
| `co2` | ppm | analog_gauge | telemetry |
| `t_voc` | ppb | analog_gauge | telemetry |
| `iaq_index` | índice 0-500 | analog_gauge | telemetry |
| `avg_sound_level` | dB | analog_gauge | telemetry |
| `max_sound_level` | dB | analog_gauge | telemetry |
| `luminosity` | lux | analog_gauge | telemetry |
| `power_01` | W | counter | telemetry (sum) |
| `temperature_supply` | °C | analog_gauge | telemetry |
| `temperature_return` | °C | analog_gauge | telemetry |
| `ac_state` / `ac_control` | bool | bool_state | state_events |
| `fan_speed_01..03_state` | bool | bool_state | state_events |
| `light_01..02_state` | bool | bool_state | state_events |
| `valve_control` / `valve_state` | bool | bool_state | state_events |
| `occupancy` | bool | bool_presence | telemetry |
| `people_count` | int 0-50 | analog_gauge | telemetry |

A nivel de site (no de aula): `temperature_outdoor`, `solar_irradiance`.
