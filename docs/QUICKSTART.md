# QUICKSTART — primer arranque paso a paso

Guía pensada para que **cualquier alumno de FP** pueda levantar el stack en
menos de 10 minutos sin saber nada de Docker. Si algo falla, ve a
[`docs/TROUBLESHOOTING.md`](./TROUBLESHOOTING.md).

> **Tiempo estimado**: 5–10 minutos la primera vez (descargas Docker).
> Despues, < 1 minuto.

---

## 0. Antes de empezar

Necesitas instalar **una sola vez**:

| Herramienta | Para qué | Instalación |
|-------------|----------|-------------|
| **Docker Desktop** | Ejecuta los contenedores (Mosquitto, InfluxDB, Grafana, etc.) | <https://www.docker.com/products/docker-desktop> |
| **Git** | Descargar el repo | <https://git-scm.com/downloads> |
| **GNU Make** | Atajos `make demo`, `make down`, etc. | Windows: `winget install GnuWin32.Make` o `scoop install make`. macOS: ya viene. Linux: `sudo apt install make` |

Si quieres además ejecutar tests Python o el generator en local también necesitarás:

| Opcional | Para qué | Instalación |
|----------|----------|-------------|
| **uv** | Gestor de paquetes Python (rápido) | `pip install uv` o ver <https://github.com/astral-sh/uv> |
| **Python 3.12** | Lo instala `uv` solo si haces `make install` | — |

---

## 1. Descargar el repo

```bash
git clone https://github.com/jaimesendra/captia-synthetic-data-bms.git
cd captia-synthetic-data-bms
```

---

## 2. Levantar todo con un solo comando

```bash
make demo
```

Esto hace:

1. Genera `.env` con contraseñas aleatorias (la primera vez).
2. Verifica que Docker está corriendo y los puertos están libres.
3. Descarga las imágenes que falten (sólo la primera vez, ~1 GB).
4. Arranca **8 contenedores**: Mosquitto, InfluxDB, Redis, Telegraf, Grafana, Prometheus, Loki, Promtail.
5. Inicializa InfluxDB con 6 buckets y 5 tareas Flux.
6. Comprueba que MQTT, InfluxDB y Grafana responden.
7. Imprime las URL para abrir en el navegador.

> Si Docker pide permisos (compartir carpetas, abrir puertos…), acepta.

---

## 3. Abrir Grafana

<http://localhost:3001>

- Usuario: `admin`
- Contraseña: `admin` (Grafana te pedirá cambiarla la primera vez; puedes saltar).

Verás un menú **Dashboards → CAPTIA-BMS** con 4 paneles:

- **BMS Overview** — métricas del propio generador.
- **BMS IAQ — Caso D** — calidad de aire (CO₂, temperatura, humedad).
- **BMS Consumo eléctrico — Caso B** — `power_01`, exterior, irradiancia.
- **BMS Fallos HVAC — Caso C** — fallos inyectados.

Aún están vacíos: necesitas el generador publicando datos (paso 4).

---

## 4. (Opcional) Hacer que entren datos sintéticos

Tienes dos opciones:

### Opción A — generar datos manualmente (rápido, sirve como demo)

```bash
make smoke-mqtt   # publica un punto de prueba al broker
```

Espera 10–15 s y refresca el dashboard *BMS Overview* en Grafana. Verás
contadores subir.

### Opción B — lanzar el generador en tu máquina

Necesitas `uv` instalado. En **otra terminal**:

```bash
make install      # crea entorno Python (sólo la primera vez)
make run-host     # arranca el generador en http://localhost:8120
```

Deja esta terminal abierta. Vuelve a la primera y:

```bash
# Lee tu BMS_API_TOKEN
TOKEN=$(grep '^BMS_API_TOKEN=' .env | cut -d= -f2)

curl -X POST http://localhost:8120/v1/control/start \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"config_path":"./config/projects/bms_v1_demo.yaml","mode":"live","aulas":3,"faults":[]}'
```

Empezarán a llegar datos cada 5 s. Refresca Grafana.

---

## 5. Parar el stack

```bash
make down       # apaga los contenedores (los datos se conservan)
```

Si quieres borrar también todos los datos guardados (volúmenes Docker):

```bash
make clean
```

---

## Comandos útiles después

```bash
make help           # lista todo
make ps             # ¿qué contenedores están vivos?
make logs           # ver logs en vivo de todos
make logs SERVICE=influxdb   # logs de un servicio
make smoke          # repite los chequeos de salud
make urls           # imprime las URLs locales otra vez
```

---

## Si algo no funciona

Lee [`docs/TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) — incluye los problemas
más típicos:

- "Docker daemon no responde" → arranca Docker Desktop.
- "puerto X ya en uso" → cambia el puerto en `.env`.
- "401 Unauthorized" en InfluxDB → ejecuta `make clean && make demo`.
- "telegraf no se conecta" → mira si `captia-network` está siendo compartida con otro proyecto.
