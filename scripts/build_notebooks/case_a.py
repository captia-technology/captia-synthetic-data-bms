"""01 Case A — Pipeline IoT CENTINELA+ (3 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_CASE_A

CASE = "A — Pipeline IoT CENTINELA+"
SPEC = "docs/specs/synthetic-bms/03-architecture-spec.md"


def _nb_01_pipeline(target: Path) -> Path:
    title = "Pipeline IoT CENTINELA+ — explicación de las 5 capas"
    sections = [
        section(
            1,
            "Objetivo",
            "Comprender de extremo a extremo cómo CENTINELA+ recibe un dato real "
            "(sensor → MQTT → Telegraf → InfluxDB → Grafana) y por qué este "
            "proyecto reproduce ese mismo flujo con un generador sintético.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Las 5 capas de CENTINELA+ y la responsabilidad de cada una.\n"
            "- Por qué Mosquitto y Telegraf no se comunican con la BD directamente.\n"
            "- Cómo se garantiza la entrega de mensajes (QoS 1, durabilidad).\n"
            "- Routing on-change vs continuo (telemetry vs state_events).\n"
            "- Vocabulario para todos los notebooks de este caso.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Caso A es el único caso de uso del proyecto que reproduce el "
            "pipeline IoT completo. El resto de equipos puede insertar directamente "
            "en InfluxDB; este equipo simula como si fuesen sensores reales.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Cada componente de este notebook es **idéntico** al desplegado en el "
            "edge server del IES Simarro. Cuando los sensores reales generen datos "
            "suficientes, basta con reorientar Telegraf al Mosquitto del edificio.",
        ),
        section(
            5,
            "Relación con Medallion",
            "El equipo del Caso A vive en la frontera **bronce → plata**. El "
            "payload MQTT que sale del sensor es bronce; lo que entra a InfluxDB es "
            "plata.",
        ),
        section(
            6,
            "Datos de entrada",
            "Conceptual: no cargamos datasets. Mostraremos un payload de ejemplo y "
            "explicaremos cómo viaja por las capas.",
        ),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "El topic MQTT y el payload JSON; la línea final en InfluxDB.",
            """\
topic = build_topic(env="dev", tenant="default", site="ies_simarro",
                    asset="AULA01", variable="co2")
payload = {"value": 712, "ts_ns": int(pd.Timestamp("2026-05-10T08:00:00Z").value)}
print("topic:", topic)
print("payload:", payload)
""",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Construimos un dataframe `flujo` que enumera cada capa, su tecnología, "
            "su responsabilidad y el formato de los datos que la atraviesan.",
            """\
flujo = pd.DataFrame(
    [
        ("1 sensores", "BME680, Sensup, gateway BMS", "publica MQTT 5s", "{value, ts_ns} JSON"),
        ("2 broker MQTT", "Mosquitto 2.0", "ACLs, QoS 1, persistencia", "topic + payload"),
        ("3 ingesta", "Telegraf 1.32", "regex 5 tags, dedup on-change", "line protocol"),
        ("4 BD series", "InfluxDB 2.7 (7 buckets)", "raw + rollups", "captia_point"),
        ("5 visualización", "Grafana 11 + Adapter", "dashboards, cache Redis", "queries Flux"),
    ],
    columns=["capa", "tecnología", "responsabilidad", "formato datos"],
)
flujo
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Pintamos un diagrama Mermaid en una celda Markdown que se renderiza en "
            "Jupyter (con la extensión correspondiente) y también en MkDocs Material.",
            """\
from IPython.display import Markdown
Markdown('''```mermaid
flowchart LR
  S[Sensor BMS\\nMQTT] --> M[Mosquitto\\nQoS 1]
  M --> T[Telegraf\\nregex + dedup]
  T --> I[(InfluxDB\\n7 buckets)]
  I --> G[Grafana\\ndashboards]
  T -. /metrics .-> P[Prometheus]
  G <-. cache .-> R[(Redis)]
```''')
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Telegraf se configura con un único bloque `mqtt_consumer` y dos outputs "
            "(uno a `telemetry`, otro a `state_events`). Reproducimos una versión "
            "minimal del fichero TOML.",
            """\
telegraf_minimal = '''
[[inputs.mqtt_consumer]]
  servers = ["tcp://mosquitto:1883"]
  topics  = ["captia/+/+/+/+/telemetry/+", "captia/+/+/+/+/event/+"]
  name_override = "captia_point"
  data_format = "json"

[[processors.regex.tags]]
  key = "topic"
  pattern = "captia/([^/]+)/([^/]+)/([^/]+)/([^/]+)/[^/]+/([^/]+)"
  result_key = "captia_env"  # idem para domain_id, site_id, asset_id, variable

[[outputs.influxdb_v2]]
  bucket = "telemetry"
  fieldpass = ["value"]
'''
print(telegraf_minimal)
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "El equipo Caso A no construye capa oro: su entregable es el pipeline. "
            "El **valor** queda en los dashboards Grafana y en la documentación.",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Pintamos un timeline ficticio de la latencia esperada por capa (ms).",
            """\
latencias_ms = pd.Series(
    {"sensor->broker": 5, "broker->telegraf": 2, "telegraf->influx": 8, "influx->grafana": 50},
)
ax = latencias_ms.plot.barh(color="#3F51B5", figsize=(7, 3))
ax.set_xlabel("ms (mediana esperada)")
ax.set_title("Latencia por capa (orden de magnitud)")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Confirmamos que el topic generado cumple el contrato (6 niveles, "
            "`telemetry` o `event`).",
            """\
assert topic.count("/") == 6
parts = topic.split("/")
assert parts[0] == "captia"
assert parts[5] in {"telemetry", "event"}
print("Topic OK:", topic)
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Cambiar el orden del topic**. Telegraf no parsea y el dato se descarta.\n"
            "2. **Olvidar `fieldpass = ['value']`**. Aparecen fields adicionales que rompen `count(_field=='value')`.\n"
            "3. **Publicar con QoS 0**. En entornos lossy los puntos se pierden silenciosamente.\n"
            "4. **No tener `captia_metadata` poblado**. Las tareas Flux de downsampling no emiten para esa variable.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade un nivel `floor` al topic y enumera los cambios necesarios en Telegraf.\n"
            "2. Diseña un payload alternativo `{value, ts}` con ISO 8601 y discute pros/contras.\n"
            "3. Calcula cuántos mensajes/segundo debe sostener Telegraf con 70 aulas y 22 variables.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cuando los sensores físicos del IES Simarro publiquen, basta con apuntar "
            "Telegraf al Mosquitto del edge server (100.102.212.105) y Telegraf "
            "escribirá en el InfluxDB local. El código no cambia.",
        ),
        common_summary(
            next_notebook="01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb",
            docs_link="docs/use-cases/case-a-pipeline-iot.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="01_case_A_pipeline_iot/01_explicacion_pipeline_centinela.ipynb",
        title=title,
        case=CASE,
        layer="bronce → plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_A,
    )


def _nb_02_publicacion(target: Path) -> Path:
    title = "Publicación MQTT a InfluxDB — del CSV al broker en velocidad acelerada"
    sections = [
        section(
            1,
            "Objetivo",
            "Tomar el mock In-Gauge de AULA01 (1 semana × 1 minuto) y publicarlo "
            "vía MQTT con topic canónico, simulando los sensores reales de "
            "CENTINELA+. Comprobar que cada mensaje aterriza en `captia_point`.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Cómo usar `paho-mqtt` para publicar en Mosquitto.\n"
            "- Estructura del payload `{value, ts_ns}`.\n"
            "- Velocidad acelerada vs tiempo real.\n"
            "- Cómo verificar la llegada con una query Flux.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Los datasets públicos tienen resolución de minutos o segundos. "
            "Esperar a que pase el tiempo real sería absurdo para una clase. La "
            "técnica habitual es **publicar tan rápido como permita el broker**, "
            "pero conservando los timestamps originales del dataset.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Reproducimos el papel del firmware del sensor. La diferencia es que "
            "publicamos a velocidad acelerada para no esperar 7 días de clase.",
        ),
        section(
            5,
            "Relación con Medallion",
            "Capa **bronce** (CSV In-Gauge) → **plata** (`captia_point` en InfluxDB).",
        ),
        section(
            6,
            "Datos de entrada",
            "`notebooks/_data/ingauge_aula01_mock.csv` (1 semana × 1min, 9 columnas).",
        ),
        setup_section(
            "Si el stack está levantado, importamos `paho.mqtt.client`. Si no, "
            "definimos un cliente mock que registra los mensajes en memoria.",
        ),
        section(
            8,
            "Schema CAPTIA esperado",
            "Para cada fila del CSV producimos varios topics MQTT (uno por variable). "
            "Mapping In-Gauge → CAPTIA según `docs/specs/synthetic-bms/02-domain-spec.md`.",
            """\
mapping_ingauge = {
    "Indoor_CO2": "co2",
    "Indoor_Temp": "temperature_01",
    "Indoor_Hum": "relative_humidity_01",
    "Indoor_Noise": "avg_sound_level",
    "Indoor_Lux": "luminosity",
    "People_Count": "people_count",
    "Occupied": "occupancy",
    "CoolingState": "ac_state",
}
mapping_ingauge
""",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos el CSV mock (con la cabecera `# MOCK ...`) y mostramos las primeras filas.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "ingauge_aula01_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Resumen estadístico del dataset y conteo por hora.",
            """\
print("Filas:", len(df), "  Variables CSV:", len(df.columns) - 1)
df.set_index("timestamp").resample("1h").mean(numeric_only=True).head()
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Construimos los mensajes MQTT (topic + payload) que vamos a publicar. "
            "Si tenemos `paho-mqtt` y el broker funciona, publicamos; si no, los "
            "ponemos en una lista en memoria que demuestra el flujo.",
            """\
def iter_mqtt_messages(df, asset="AULA01", env="dev", tenant="default", site="ies_simarro"):
    for _, row in df.iterrows():
        ts_ns = int(pd.Timestamp(row["timestamp"]).value)
        for csv_col, captia_var in mapping_ingauge.items():
            if csv_col not in row or pd.isna(row[csv_col]):
                continue
            topic = build_topic(env=env, tenant=tenant, site=site,
                                 asset=asset, variable=captia_var)
            payload = {"value": float(row[csv_col]), "ts_ns": ts_ns}
            yield topic, payload

# Para clase: tomamos solo los primeros 200 mensajes (~25 filas) para no saturar
muestras = list(iter_mqtt_messages(df.head(25)))
print(f"Generados {len(muestras)} mensajes MQTT (primeros 25 minutos del mock)")
muestras[0]
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "**Publicación real** con `paho-mqtt` si el broker está disponible. Si no, "
            "registramos en memoria y medimos el throughput de generación. En ambos "
            "modos reportamos `msgs/s`.",
            """\
import os, time

published = []
mqtt_status = "in_memory"
broker_host = os.environ.get("MQTT_HOST", "localhost")
broker_port = int(os.environ.get("MQTT_PORT_HOST", os.environ.get("MQTT_PORT", "1884")))

t0 = time.perf_counter()
try:
    import paho.mqtt.client as mqtt
    client = mqtt.Client(client_id="captia-bms-notebook-a02",
                         callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.connect(broker_host, broker_port, keepalive=30)
    client.loop_start()
    for topic, payload in muestras:
        client.publish(topic, json.dumps(payload), qos=1)
        published.append((topic, payload))
    # Pequeña espera para drenar el buffer in-flight
    time.sleep(0.2)
    client.loop_stop()
    client.disconnect()
    mqtt_status = f"published_to_{broker_host}:{broker_port}"
except (ImportError, ConnectionRefusedError, OSError) as e:
    # Fallback: simulamos sin broker
    for topic, payload in muestras:
        published.append((topic, payload))
    mqtt_status = f"in_memory_fallback ({type(e).__name__})"

import json  # asegurar import si fallback se usó antes
elapsed = time.perf_counter() - t0
throughput = len(published) / max(elapsed, 1e-3)
print(f"{len(published)} mensajes en {elapsed:.3f}s = {throughput:.0f} msg/s · status={mqtt_status}")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "**3 paneles**: distribución por variable, timeline de publicación y "
            "throughput acumulado vs teórico (CENTINELA+ real ≈ 308 msg/s).",
            """\
import collections
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(13, 4))

counts = collections.Counter(t.split("/")[-1] for t, _ in published)
pd.Series(counts).sort_values().plot.barh(ax=axes[0], color="#3F51B5")
axes[0].set_title(f"Mensajes por variable (total {len(published)})")

ts_seq = [pd.Timestamp(p["ts_ns"], unit="ns") for _, p in published]
axes[1].eventplot([t.timestamp() for t in ts_seq], color="#FF5722", lineoffsets=1)
axes[1].set_title("Timeline ts_ns publicaciones")
axes[1].set_yticks([])

# Throughput acumulado
n_per_s = pd.Series(1, index=range(len(published))).cumsum()
axes[2].plot(n_per_s.index, n_per_s.values, color="#4CAF50", label="acumulado")
axes[2].axhline(308, color="gray", linestyle="--", label="lambda teorico CENTINELA+ (308 msg/s)")
axes[2].set_title(f"Throughput medido: {throughput:.0f} msg/s")
axes[2].set_xlabel("nº mensaje"); axes[2].legend(loc="lower right", fontsize=8)
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Comprobamos que: cada topic tiene 6 niveles, el payload tiene los 2 "
            "campos requeridos, los timestamps son monotónicos por variable.",
            """\
import json

assert all(t.count("/") == 6 for t, _ in muestras)
assert all(set(p.keys()) == {"value", "ts_ns"} for _, p in muestras)

# Monotonicidad por (topic)
prev_ts = {}
for topic, payload in muestras:
    if topic in prev_ts:
        assert payload["ts_ns"] >= prev_ts[topic]
    prev_ts[topic] = payload["ts_ns"]
print("Validaciones OK · ejemplos:")
for topic, payload in muestras[:3]:
    print(f"  {topic} → {json.dumps(payload)}")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **No esperar entre `connect` y `publish`** — el cliente puede no haber "
            "completado el handshake.\n"
            "2. **Publicar a 1 Hz pero el broker rechaza** — confirmar QoS 1 y "
            "configurar `max_inflight_messages` en el cliente.\n"
            "3. **Olvidar `client.loop_start()`** — sin loop, los ACKs no se procesan.\n"
            "4. **Usar `time.sleep(60)` para simular tiempo real** — la clase dura 50 "
            "minutos, no 7 días.\n"
            "5. **Confundir `value` con `value_str`** — InfluxDB rechaza tipos mixtos.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `valve_state` al mapping y publícala.\n"
            "2. Implementa `publish_with_backpressure(client, msgs, target_rate)` que "
            "envía a `target_rate` msgs/s usando `time.sleep`.\n"
            "3. Simula una pérdida del 5% de mensajes y mide el impacto.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Para enviar telemetría real basta con cambiar `MQTT_HOST` en `.env` y "
            "leer del topic real. La función `iter_mqtt_messages` se reusa palabra por "
            "palabra; solo cambia el origen de los datos.",
        ),
        common_summary(
            next_notebook="01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb",
            docs_link="docs/contracts/mqtt-topics.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb",
        title=title,
        case=CASE,
        layer="bronce → plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_A,
    )


def _nb_03_validacion(target: Path) -> Path:
    title = "Validación Telegraf → InfluxDB → Grafana"
    sections = [
        section(
            1,
            "Objetivo",
            "Verificar que los mensajes publicados en el notebook anterior han "
            "llegado a InfluxDB con `captia_point`, los 5 tags correctos y el field "
            "`value` numérico.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Cómo escribir queries Flux en Python.\n"
            "- Cómo confirmar el schema canónico desde el cliente.\n"
            "- Cómo invalidar un dataset (revertir, no editar) si algo está mal.\n"
            "- Cómo verificar el funcionamiento de los rollups.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Una vez se publica, el equipo Caso A debe demostrar que los dashboards "
            "de Grafana y los downsamples a 1m / 15m / 1h funcionan correctamente. "
            "Esta validación se hace con queries Flux ejecutadas desde Python.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Las queries que escribimos aquí son las mismas que ejecutará el "
            "Dashboard Adapter en producción cuando un alumno consulte AULA01 desde "
            "el chatbot del Caso H.",
        ),
        section(
            5,
            "Relación con Medallion",
            "Estamos en la **capa plata**. La transformación bronce → plata ya "
            "ocurrió; aquí auditamos su correcto funcionamiento.",
        ),
        section(
            6,
            "Datos de entrada",
            "InfluxDB con los datos publicados. Si trabajamos en modo offline, "
            "construimos el resultado esperado a mano para comparar.",
        ),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "El resultado de la query debe contener filas con `captia_env=dev`, "
            "`domain_id=bms_classrooms`, `site_id=ies_simarro`, `asset_id=AULA01`, "
            "`variable=<algo>`, `_field=value`, `_value=<float>`.",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Si el cliente está disponible, ejecutamos la query Flux contra el "
            "bucket `telemetry`. Si estamos offline, mostramos el resultado esperado.",
            """\
client = get_influx_client()
flux = '''
from(bucket: "telemetry")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "captia_point")
  |> filter(fn: (r) => r.asset_id == "AULA01")
  |> filter(fn: (r) => r.variable == "co2")
  |> limit(n: 5)
'''

if client is not None:
    df_query = client.query_api().query_data_frame(flux, org=os.environ.get("INFLUXDB_ORG", "captia"))
    if isinstance(df_query, list):
        df_query = pd.concat(df_query, ignore_index=True) if df_query else pd.DataFrame()
else:
    df_query = pd.DataFrame(
        {
            "_measurement": ["captia_point"] * 3,
            "captia_env": ["dev"] * 3,
            "domain_id": ["bms_classrooms"] * 3,
            "site_id": ["ies_simarro"] * 3,
            "asset_id": ["AULA01"] * 3,
            "variable": ["co2"] * 3,
            "_field": ["value"] * 3,
            "_value": [705.0, 712.5, 720.1],
            "_time": pd.date_range("2026-05-10", periods=3, freq="60s", tz="UTC"),
        }
    )
df_query.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Comprobamos las columnas devueltas y la cardinalidad de tags.",
            """\
import os

print("Columnas devueltas:", list(df_query.columns))
for tag in ["captia_env", "domain_id", "site_id", "asset_id", "variable"]:
    if tag in df_query.columns:
        print(f"  {tag} =", df_query[tag].unique()[:5])
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "No aplica — auditamos la plata existente.",
        ),
        section(
            12,
            "Construcción de capa oro",
            "Como tarea didáctica, calculamos un agregador horario que sería "
            "idéntico al downsample de Influx. Esto sirve para entender qué hace "
            "el bucket `telemetry_1m`.",
            """\
if not df_query.empty and "_time" in df_query.columns and "_value" in df_query.columns:
    serie = df_query.set_index("_time")["_value"].resample("1min").mean()
    print(serie.head())
else:
    print("Sin datos: revisar publicación o conexión.")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Plot de la serie agregada (si hay datos).",
            """\
if not df_query.empty:
    plot_timeseries(df_query.rename(columns={"_time": "timestamp"}), value_cols=["_value"], title="CO2 AULA01 — capa plata")
    plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Las dos validaciones canónicas: 5 tags presentes y field único.",
            """\
required = set(CANONICAL_TAGS)
present = set(df_query.columns) & required
missing = required - present
assert not missing, f"Tags canónicos ausentes: {missing}"

field_col = df_query.get("_field")
if field_col is not None:
    assert (field_col == "value").all(), "Solo se admite field='value'"
print("Validaciones OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **`influx_query` devuelve vacío**: confirmar `range(start)` y "
            "`asset_id`.\n"
            "2. **Field múltiple**: si aparece más de un `_field`, hay datos legacy.\n"
            "3. **Tags vacíos**: el regex de Telegraf falló; revisar `topic` malformado.\n"
            "4. **Hora UTC vs local**: Grafana puede mostrar Madrid; los timestamps "
            "internos son siempre UTC.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Escribe una query Flux que cuente puntos por aula en la última "
            "hora.\n"
            "2. Modifica la query para devolver solo `state_events`.\n"
            "3. Construye un dashboard Grafana con CO₂ y `ac_state` superpuestos.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "El mismo notebook funciona sobre `simarro-prod`: cambiar `INFLUXDB_URL` "
            "y `INFLUXDB_TOKEN` en `.env`, y la query devuelve datos reales.",
        ),
        common_summary(
            next_notebook="02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb",
            docs_link="docs/use-cases/case-a-pipeline-iot.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb",
        title=title,
        case=CASE,
        layer="plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_A,
    )


def build(target: Path) -> int:
    _nb_01_pipeline(target)
    _nb_02_publicacion(target)
    _nb_03_validacion(target)
    return 3
