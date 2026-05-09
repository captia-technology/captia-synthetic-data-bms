# Troubleshooting

Lista de problemas reales que ya nos hemos encontrado, con la solución
exacta. Si tu problema no está aquí, abre un *issue* con la salida de
`make ps` y `docker logs <servicio>`.

---

## 1. `docker daemon is not running`

**Síntoma**: cualquier comando de `docker` (o `make demo`) falla con
`error during connect: ... open //./pipe/dockerDesktopLinuxEngine: ...` o
similar.

**Causa**: Docker Desktop no está iniciado.

**Fix**: arranca Docker Desktop desde el menú de Windows / Applications de
macOS / `systemctl start docker` en Linux. Espera ~30 s a que el icono se
ponga verde, luego reintenta.

---

## 2. `port is already allocated`

**Síntoma**:
```
Bind for 0.0.0.0:9002 failed: port is already allocated
```

**Causa**: otra cosa (otro Mosquitto, otro Grafana, otro InfluxDB) ya
está usando ese puerto en tu host. Suele pasar si tienes el repo
**CAPTIA-CONNECT** corriendo a la vez.

**Fix**: edita `.env` y cambia el puerto. Por ejemplo:

```bash
MQTT_WS_PORT_HOST=9102      # antes 9002
GRAFANA_PORT_HOST=3001      # ya viene en 3001 por defecto
```

Después: `make down && make demo`.

---

## 3. `pull access denied` o `failed to copy: httpReadSeeker`

**Síntoma**: al construir o levantar contenedores nuevos, Docker se queda
colgado intentando descargar una imagen y falla con un timeout contra
`docker-images-prod.cloudflarestorage.com`.

**Causa**: tu red bloquea (o tiene problemas con) el CDN de Docker Hub.

**Fix opciones**:

- Si estás en una **red corporativa**: usa una VPN o conecta el móvil.
- Configura un **mirror** en Docker Desktop → Settings → Docker Engine:
  ```json
  { "registry-mirrors": ["https://mirror.gcr.io"] }
  ```
- Espera 10 minutos: a veces Cloudflare R2 está saturado puntualmente.
- Si solo te falta `python:3.12-slim` (necesario para construir el
  generator), usa `make demo` en lugar de `make quickstart`. Levanta
  toda la infra con imágenes pre-cacheadas y deja el generator para
  ejecutarlo en local con `make run-host`.

---

## 4. InfluxDB devuelve `401 Unauthorized` desde Telegraf

**Síntoma**: en `docker logs captia-bms-telegraf` aparece:
```
failed to write metric to telemetry (401 Unauthorized)
```

**Causa más frecuente**: tienes otro repo CAPTIA con su propio InfluxDB
en la **misma red Docker** (`captia-network`). Cuando tu stack hace DNS
sobre `influxdb`, Docker resuelve al InfluxDB del otro proyecto, que tiene
un token distinto.

**Fix**: edita `.env` para usar una red dedicada:

```bash
CAPTIA_NETWORK_NAME=captia-bms-network
```

Después: `make clean && make demo` (el `clean` borra el volumen, lo cual
es necesario para que InfluxDB se reinicialice con el token correcto).

> En `.env.example` ya viene con este valor por defecto.

---

## 5. Grafana se queda en `health: starting`

**Síntoma**: `make ps` muestra `captia-bms-grafana ... (health: starting)`
durante más de 30 s.

**Causa**: Grafana tarda en arrancar la primera vez (instala el plugin
`redis-datasource`).

**Fix**: espera. Si pasados 90 s sigue starting, mira los logs:

```bash
make logs SERVICE=grafana
```

---

## 6. Bucket `telemetry` se queda vacío aunque publico

**Síntoma**: ejecuto `make smoke-mqtt`, espero, pero
`make smoke-schema` no encuentra los tags.

**Causas posibles**:

1. El timestamp del payload está fuera del retention del bucket
   (`telemetry` retiene 14 días). Solución: el script
   `scripts/smoke_mqtt.sh` ya usa `date +%s` automáticamente.
2. Telegraf está conectado a otro broker / otra InfluxDB
   (ver problema **#4**).
3. El topic publicado no encaja con la regex de Telegraf.
   Formato correcto:
   ```
   captia/{captia_env}/{domain_id}/{site_id}/{asset_id}/telemetry/{variable}
   ```
   El segmento 2 *NO* es `default` ni `tenant` arbitrario; debe ser
   `bms_classrooms` para que el tag `domain_id` salga correcto.

---

## 7. `influx-init` exit code 1: `could not resolve org id`

**Síntoma**: `docker logs captia-bms-influx-init` muestra:
```
ERROR: could not resolve org id for org=captia
```

**Causa**: el token admin que tu `.env` proporciona no coincide con el
que InfluxDB tiene cargado en su volumen persistente. Es lo que pasa
cuando reinstalas el repo sin borrar volúmenes previos.

**Fix**:

```bash
make clean      # borra volúmenes
make demo       # vuelve a inicializar todo con el token actual
```

---

## 8. `uv sync` o `make install` falla

**Síntoma**: `uv: command not found` o errores instalando paquetes.

**Fix**:

- Instala `uv`: `pip install uv` o
  `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- Asegúrate de tener Python 3.12 disponible (uv lo instala si falta).
- Si no necesitas correr el generator en local, **puedes saltarte
  `make install`** y limitarte a `make demo` (solo Docker).

---

## 9. "no se ven dashboards en Grafana"

**Síntoma**: entro en Grafana y la sección *Dashboards* está vacía.

**Causa**: los dashboards se cargan vía provisioning y aparecen bajo
una *folder*. Mira en *Dashboards → Browse → CAPTIA-BMS*.

Si ahí tampoco hay nada:

- `docker logs captia-bms-grafana` debería mostrar
  `provisioning/dashboards/...`.
- Si no, comprueba que la carpeta `infra/grafana/dashboards/` existe en tu
  checkout (a veces Windows con permisos restrictivos no la monta).

---

## 10. `gitleaks` o `pre-commit` rechaza un commit

**Síntoma**: `git commit` aborta con un detector de secretos.

**Fix**: revisa qué secreto detectó. La mayor parte de las veces es un
token de prueba dentro de un test. Si confirmas que el valor es de prueba
y no real, añádelo a `.gitleaks.toml` (o sustitúyelo por una constante
obvia tipo `dummy-test-token`). NUNCA hagas `--no-verify` para
saltártelo.

---

## ¿Aún no funciona?

1. `docker info | head -20`
2. `make ps`
3. `docker logs captia-bms-influxdb 2>&1 | tail -30`
4. Abre un issue con esa salida y describe exactamente qué comando lanzaste.
