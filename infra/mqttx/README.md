# MQTTX-Web — Cliente MQTT preconfigurado

UI MQTT en `http://localhost:${MQTTX_WEB_PORT_HOST:-8083}/` (servida por el contenedor `captia-bms-mqttx-web`, ver `compose/observability.yaml`).

> MQTTX-Web es una **SPA** que guarda su configuración en `localStorage` del navegador. Por eso la conexión no se "auto-provisiona" desde el servidor — pero dejamos un fichero de import listo para cargarlo en un click.

---

## Importar conexión + suscripciones + scripts (1 minuto)

1. Abre `http://localhost:8083/`.
2. Pulsa el icono ⚙️ (Settings, esquina inferior izquierda).
3. **Data → Import Data → Choose file** y selecciona:
   ```
   infra/mqttx/captia-bms-mqttx-config.json
   ```
   El fichero también está disponible en raw vía:
   `http://localhost:8083/captia-bms-mqttx-config.json` *(si lo montas como volumen — opcional)*.
4. Acepta. Verás aparecer:
   - Conexión **`CAPTIA BMS · local (WebSocket)`** apuntando a `ws://localhost:9102/mqtt`.
   - 7 suscripciones predefinidas (`captia/#`, telemetría general, temperature_01, co2, power_01, iaq-index, eventos).
   - 2 scripts (`decode-captia-payload`, `publish-fault-example`).
5. Click en la conexión → **Connect**. Empezarás a ver los mensajes en vivo.

---

## Suscripciones incluidas

| Alias | Topic pattern | Qué muestra |
|-------|---------------|-------------|
| `all-captia` | `captia/#` | Todo el árbol (firehose) |
| `telemetry-aulas` | `captia/dev/bms_classrooms/ies_simarro/+/telemetry/+` | Solo telemetría de cualquier aula y variable |
| `temperature-only` | `…/+/telemetry/temperature_01` | Sondas de temperatura |
| `co2-only` | `…/+/telemetry/co2` | CO₂ por aula |
| `power-only` | `…/+/telemetry/power_01` | Potencia eléctrica |
| `iaq-only` | `…/+/telemetry/iaq-index` | Índice IAQ calculado |
| `events-and-faults` | `…/+/event/+` | Averías y eventos discretos |

---

## Schema de payload CAPTIA

Todos los mensajes usan el mismo formato (regla 002 — schema canónico):

```json
{ "value": 23.45, "ts_ns": 1778424694000000000 }
```

- `value`: float (estados booleanos como `1.0` / `0.0`).
- `ts_ns`: epoch en **nanosegundos**.

El topic sigue 7 segmentos:
```
captia/{env}/{tenant}/{site}/{device}/{stream}/{name}
captia/dev /bms_classrooms/ies_simarro/AULA01/telemetry/temperature_01
```

---

## Ejemplos de lectura

### Suscripción puntual con CLI

Sin abrir UI:
```powershell
docker exec captia-bms-mosquitto mosquitto_sub -h localhost -p 1883 -t "captia/#" -v
```

Solo una variable:
```powershell
docker exec captia-bms-mosquitto mosquitto_sub `
  -h localhost -p 1883 `
  -t "captia/dev/bms_classrooms/ies_simarro/+/telemetry/co2" -v
```

### Publicar manual (probar el pipeline)

```powershell
docker exec captia-bms-mosquitto mosquitto_pub `
  -h localhost -p 1883 `
  -t "captia/dev/bms_classrooms/ies_simarro/TEST_AULA/telemetry/temperature_01" `
  -m '{"value": 22.5, "ts_ns": 1778424694000000000}'
```

### Decodificador en MQTTX-Web

El script `decode-captia-payload` (incluido en el JSON) parsea cada payload y muestra:

```json
{
  "aula": "AULA01",
  "variable": "temperature_01",
  "value": 18.41,
  "ts": "2026-05-10T12:34:54.000Z"
}
```

Para activarlo: en el panel de mensajes recibidos, **Function → decode-captia-payload**.

---

## Troubleshooting

| Síntoma | Causa probable | Fix |
|---------|----------------|-----|
| `Connection refused` al conectar | Puerto 9102 no está mapeado | `docker ps \| grep mosquitto` debe mostrar `9102->9001/tcp` |
| Conecta pero **0 mensajes** | El generator no está publicando | `docker logs captia-bms-generator --tail 20` o `make demo:publish` |
| WebSocket handshake falla | Mosquitto sin `protocol websockets` en config | Ver `infra/mosquitto/mosquitto.conf:10-11` |
| Browser cachea config vieja | localStorage stale | DevTools → Application → Storage → Clear site data |

---

## Variables de entorno relevantes (`.env`)

```bash
MQTT_WS_PORT_HOST=9102      # WebSocket exposed por Mosquitto
MQTTX_WEB_PORT_HOST=8083    # UI MQTTX-Web
```
