"""00 Project overview — 3 notebooks fundacionales."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_OVERVIEW

CASE = "Overview"
SPEC = "docs/specs/synthetic-bms/01-product-spec.md"


def _nb_00_arquitectura(target: Path) -> Path:
    title = "Arquitectura Medallion aplicada a CAPTIA Synthetic Data BMS"
    sections = [
        section(
            1,
            "Objetivo",
            "Entender en 30 minutos cómo se organizan los datos del proyecto en las "
            "tres capas Medallion (bronce → plata → oro), por qué CAPTIA tiene una "
            "capa plata canónica (`captia_point` + 5 tags + `value`) y cómo encaja "
            "cada caso de uso del proyecto en esta arquitectura.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Definición precisa de cada capa Medallion.\n"
            "- Diferencia entre Medallion estricto, distribuido e híbrido.\n"
            "- Por qué el InfluxDB de simarro-prod ya es **una capa plata**.\n"
            "- Cómo cada caso de uso (A–J) se proyecta en bronce / plata / oro.\n"
            "- Vocabulario que usaremos en todos los demás notebooks.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El proyecto del Curso de Especialización IA & Big Data del IES Simarro "
            "trabaja con datos de edificios inteligentes. La estrategia de datos "
            "adoptada (mayo 2026) es **Medallion híbrida**: cada equipo construye "
            "una capa plata local con el schema canónico CAPTIA, lo que permite "
            "trabajar en paralelo sin bloqueos y consolidar al final del proyecto "
            "sin reescribir el código.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "CENTINELA+ ya tiene resuelto el paso bronce → plata para sensores reales: "
            "los sensores publican payloads MQTT que Telegraf normaliza y escribe en "
            "InfluxDB con el schema canónico. Cuando los datos del IES Simarro estén "
            "disponibles, los modelos entrenados sobre nuestra capa plata sintética "
            "deben cambiar **solo la URL y el token** del cliente InfluxDB (no el "
            "código).",
        ),
        section(
            5,
            "Relación con Medallion",
            "Diagrama:\n\n"
            "```mermaid\n"
            "flowchart LR\n"
            "  B[CAPA BRONCE\\nCSV / NetCDF / JPEG] --> S[CAPA PLATA\\ncaptia_point + 5 tags + value]\n"
            "  S --> O1[ORO Caso B\\nfeatures forecast]\n"
            "  S --> O2[ORO Caso C\\nIF/AE + labels]\n"
            "  S --> O3[ORO Caso D\\npivot IAQ + occupancy]\n"
            "  S --> O4[ORO Caso H\\ntools + RAG]\n"
            "```\n",
        ),
        section(
            6,
            "Datos de entrada",
            "Este notebook es **conceptual**: no carga ningún dataset. Visualizaremos "
            "tablas comparando capas y un Mermaid resumen de los 11 casos.",
        ),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Aunque no hagamos ETL, fijamos las constantes que aparecerán en todos "
            "los notebooks siguientes.",
            """\
print("MEASUREMENT:", MEASUREMENT_TELEMETRY)
print("CANONICAL TAGS:", CANONICAL_TAGS)
print("BUCKETS:", list(DEFAULT_BUCKET_RETENTIONS.keys()))
""",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Construimos en memoria una tabla resumen con los 11 casos para guiar el "
            "resto del proyecto. No hay descargas externas.",
            """\
casos = pd.DataFrame(
    [
        ("A", "Pipeline IoT", "MQTT → Telegraf → InfluxDB", "telemetry", "dashboards Grafana"),
        ("B", "Forecast consumo 24h", "BDG2 + UCI", "bms_buildings + bms_classrooms", "features + SARIMA/XGB"),
        ("C", "Anomalías HVAC", "LBNL FDD + sintético", "captia_fault_labels", "Isolation Forest + AE"),
        ("D", "IAQ + ocupación", "In-Gauge + UCI Occ", "telemetry 1m", "Random Forest"),
        ("E", "Meteorología solar", "ERA5 + AEMET", "weather_station/xativa", "predictor solar"),
        ("F", "MLOps", "(transversal)", "(transversal)", "MLflow + lakeFS"),
        ("G", "Calidad con agentes", "GE + reglas Flux", "todas las capas", "agentes evaluadores"),
        ("H", "RAG + Chatbot", "InfluxDB + docs", "(consume plata)", "tools + RAG"),
        ("I", "Spark vs Pandas", "BDG2 53M filas", "subset → Caso B", "benchmark"),
        ("J", "Tráfico YOLO", "JPEG DGT + AEMET", "traffic_cameras", "predicción congestión"),
        ("Extra", "Test calidad chatbot", "golden set", "(consume H)", "scoring"),
    ],
    columns=["caso", "objetivo", "bronce", "plata", "oro"],
)
casos
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Comparamos las características de las tres capas en una tabla.",
            """\
capas = pd.DataFrame(
    {
        "Bronce": [
            "datos crudos en su formato original",
            "puede tener nulos, duplicados, unidades distintas",
            "se versiona; nunca se modifica",
        ],
        "Plata": [
            "schema canónico captia_point",
            "5 tags + field value, unidades SI",
            "alimentada por ETL; consumida por modelos",
        ],
        "Oro": [
            "datasets específicos por caso de uso",
            "features ML, embeddings, agregaciones",
            "evolutiva; vive cerca del modelo",
        ],
    },
    index=["¿Qué contiene?", "Reglas", "Quién la usa"],
)
capas
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Un fragmento muestra cómo construiríamos una línea de line-protocol "
            "desde un sensor mock; reaparecerá en notebooks operacionales.",
            """\
ts_ns = int(pd.Timestamp("2026-05-10T12:00:00Z").value)
linea = build_line_protocol(
    measurement=MEASUREMENT_TELEMETRY,
    tags={
        "captia_env": "dev",
        "domain_id": "bms_classrooms",
        "site_id": "ies_simarro",
        "asset_id": "AULA01",
        "variable": "co2",
    },
    fields={"value": 712.5},
    timestamp_ns=ts_ns,
)
print(linea)
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "La capa oro es **caso-específica**: features ML para forecasting, "
            "embeddings para RAG, datasets etiquetados para detección de anomalías. "
            "No la construimos aquí — cada caso le dedica un notebook propio.",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Visualizamos cuántos notebooks tiene cada caso (mostraremos el plan de "
            "ejecución del proyecto).",
            """\
counts = pd.Series(
    {
        "00 Overview": 3, "A Pipeline IoT": 3, "B Forecast": 5,
        "C Anomalías": 5, "D IAQ": 5, "E Meteo": 4,
        "F MLOps": 3, "G Calidad": 4, "H RAG": 5,
        "I Spark": 4, "J Tráfico": 4,
    },
    name="notebooks por caso",
)
ax = counts.sort_values().plot.barh(figsize=(8, 4), color="#3F51B5")
ax.set_xlabel("notebooks")
ax.set_title("Plan didáctico — 42 notebooks")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Comprobamos que las constantes están bien expuestas y que los buckets "
            "esperados aparecen.",
            """\
assert MEASUREMENT_TELEMETRY == "captia_point"
assert set(CANONICAL_TAGS) == {"captia_env", "domain_id", "site_id", "asset_id", "variable"}
assert "telemetry" in DEFAULT_BUCKET_RETENTIONS
print("Schema canónico OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Modificar el measurement.** Cambiar `captia_point` rompe Telegraf y los dashboards.\n"
            "2. **Usar `value_<tipo>`.** Solo existe el field `value` (float).\n"
            "3. **Cardinalidad alta de tags.** Los 5 tags son indexados; añadir un sexto causa explosión de series.\n"
            "4. **Mezclar continuos y on-change en un mismo bucket.** Los `_state` van a `state_events`.\n"
            "5. **Hardcodear tokens.** Siempre usar `.env`.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Para cada caso de la tabla `casos`, identifica un dataset público alternativo válido.\n"
            "2. Construye un line-protocol para `power_01` con valor 850 W.\n"
            "3. Explica por qué `state_events` tiene 90 días y `telemetry` solo 14.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cuando CAPTIA proporcione un dump real de InfluxDB, el cambio para "
            "todos los notebooks es:\n\n"
            "1. `influx restore` del dump en el bucket `telemetry`.\n"
            "2. Actualizar `INFLUXDB_URL` y `INFLUXDB_TOKEN` en `.env`.\n"
            "3. Re-ejecutar las celdas de query — el resultado pasa de mock a real.\n",
        ),
        common_summary(
            next_notebook="00_project_overview/01_schema_captia_influxdb.ipynb",
            docs_link="docs/architecture/medallion.md",
            extra_bullets=("Recordar `seed=42` y schema canónico al iniciar cualquier notebook.",),
        ),
    ]
    return emit(
        target=target,
        rel_path="00_project_overview/00_arquitectura_medallion_captia.ipynb",
        title=title,
        case=CASE,
        layer="transversal",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_OVERVIEW,
    )


def _nb_01_schema(target: Path) -> Path:
    title = "Schema canónico CAPTIA en InfluxDB — measurement, tags, field, buckets"
    sections = [
        section(
            1,
            "Objetivo",
            "Aprender a leer y construir el schema canónico CAPTIA: measurement "
            "`captia_point`, 5 tags indexados, field `value` y los 7 buckets con "
            "sus retenciones. Trabajar con line protocol y validar la cardinalidad.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Estructura de InfluxDB 2.7 (measurement, tag, field).\n"
            "- Por qué CAPTIA usa **un solo measurement** en lugar de uno por variable.\n"
            "- Cómo se mapea un payload MQTT a una línea de line protocol.\n"
            "- Qué bucket destino corresponde a cada `metric_kind`.\n"
            "- Cómo validar el schema con `validate_canonical_tags`.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Toda la telemetría continua de CENTINELA+ vive en `captia_point`. La "
            "variable que se mide se identifica por el tag `variable`, no por el "
            "nombre del field. Esta decisión mantiene la cardinalidad baja y permite "
            "añadir variables nuevas sin tocar el schema.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "El gateway BMS de AULA01 publica cada 5 segundos en topics como "
            "`captia/prod/default/ies_simarro/AULA01/telemetry/co2`. Telegraf parsea "
            "el topic con una regex de 5 grupos y emite a InfluxDB la línea correspondiente.",
        ),
        section(
            5,
            "Relación con Medallion",
            "Este notebook es la **especificación operacional de la capa plata**. "
            "Toda transformación bronce → plata produce líneas como las de aquí.",
        ),
        section(
            6,
            "Datos de entrada",
            "Construiremos manualmente 3 puntos sintéticos para AULA01 y los "
            "imprimiremos en line protocol.",
        ),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Importamos las constantes del repo y mostramos los 7 buckets.",
            """\
import json
print("MEASUREMENT:", MEASUREMENT_TELEMETRY)
print("CANONICAL TAGS:", CANONICAL_TAGS)
print("FAULT LABELS MEASUREMENT:", MEASUREMENT_FAULT_LABELS)
print(json.dumps(DEFAULT_BUCKET_RETENTIONS, indent=2))
""",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Generamos 3 puntos: CO₂ a 712 ppm, T_indoor a 22.4 °C y un `ac_state` "
            "que se enrutará a `state_events`.",
            """\
puntos_mock = [
    {
        "topic": build_topic(env="dev", tenant="default", site="ies_simarro",
                              asset="AULA01", variable="co2"),
        "ts_ns": int(pd.Timestamp("2026-05-10T08:00:00Z").value),
        "value": 712.0,
        "metric_kind": "analog_gauge",
    },
    {
        "topic": build_topic(env="dev", tenant="default", site="ies_simarro",
                              asset="AULA01", variable="temperature_01"),
        "ts_ns": int(pd.Timestamp("2026-05-10T08:00:00Z").value),
        "value": 22.4,
        "metric_kind": "analog_gauge",
    },
    {
        "topic": build_topic(env="dev", tenant="default", site="ies_simarro",
                              asset="AULA01", variable="ac_state"),
        "ts_ns": int(pd.Timestamp("2026-05-10T08:00:00Z").value),
        "value": 1.0,
        "metric_kind": "bool_state",
    },
]
puntos_mock
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Convertimos cada punto en line protocol y validamos los tags.",
            """\
def to_line(p):
    parts = p["topic"].split("/")
    tags = {
        "captia_env": parts[1], "domain_id": "bms_classrooms",
        "site_id": parts[3], "asset_id": parts[4], "variable": parts[6],
    }
    validate_canonical_tags(tags)
    return build_line_protocol(
        measurement=MEASUREMENT_TELEMETRY, tags=tags,
        fields={"value": float(p["value"])}, timestamp_ns=p["ts_ns"],
    )

for p in puntos_mock:
    print(to_line(p))
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Las señales `_state` viajan por el mismo topic pero Telegraf las "
            "duplica al bucket `state_events` con dedup (solo en cambios de valor). "
            "Mostramos cómo se decide.",
            """\
def bucket_destino(metric_kind: str) -> str:
    if metric_kind in {"bool_state", "setpoint_step"}:
        return "state_events"
    return "telemetry"

for p in puntos_mock:
    print(p["topic"].split("/")[-1], "->", bucket_destino(p["metric_kind"]))
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "No aplica para este notebook (focalizado en la capa plata).",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Pintamos un diagrama de cardinalidad para mostrar cómo crecen las "
            "series cuando añadimos un nuevo `asset_id`.",
            """\
def n_series(asset_count: int, variables: int = 22) -> int:
    return asset_count * variables  # 5 tags fijos, solo asset_id y variable varían

asset_grid = list(range(1, 21))
series = [n_series(a) for a in asset_grid]
plt.figure(figsize=(7, 3))
plt.plot(asset_grid, series, marker="o", color="#3F51B5")
plt.title("Cardinalidad: asset_id × variable")
plt.xlabel("número de aulas")
plt.ylabel("series únicas")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Confirmamos que el schema construido cumple las invariantes del repo.",
            """\
assert MEASUREMENT_TELEMETRY == "captia_point"
assert set(CANONICAL_TAGS) == {"captia_env", "domain_id", "site_id", "asset_id", "variable"}
linea = to_line(puntos_mock[0])
assert linea.startswith("captia_point,")
assert "captia_env=dev" in linea
assert "value=712.0" in linea
print("Schema OK:", linea)
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Tag faltante**: si Telegraf falla al parsear el topic, ese punto se "
            "descarta silenciosamente. Verificar con `select(stat=count)` por aula.\n"
            "2. **Tipos inconsistentes**: si una variable se publica a veces como int "
            "y a veces como float, InfluxDB rechazará puntos.\n"
            "3. **Cardinalidad explosiva**: añadir un tag `room_color` con 200 valores "
            "diferentes infla la TSDB.\n"
            "4. **Topic incorrecto**: omitir `/telemetry/` en el medio invalida el routing.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Construye line protocol para una variable nueva `air_change_per_hour`.\n"
            "2. Modifica `validate_canonical_tags` para hacer la advertencia de tags "
            "extras un error duro.\n"
            "3. Escribe una función `parse_topic(topic)` que extraiga los 5 tags.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Para `simarro-prod` los tags son idénticos; solo cambia `captia_env=prod`. "
            "Las queries Flux que escribiremos en notebooks posteriores funcionan tal cual.",
        ),
        common_summary(
            next_notebook="00_project_overview/02_conexion_influxdb_y_variables_entorno.ipynb",
            docs_link="docs/contracts/influx-schema.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="00_project_overview/01_schema_captia_influxdb.ipynb",
        title=title,
        case=CASE,
        layer="plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_OVERVIEW,
    )


def _nb_02_conexion(target: Path) -> Path:
    title = "Conexión a InfluxDB con variables de entorno y `.env`"
    sections = [
        section(
            1,
            "Objetivo",
            "Disponer de una plantilla reutilizable para conectar con InfluxDB "
            "leyendo `.env`. Sin secretos en código. Un fallback claro para clase si "
            "el stack no está levantado.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Cómo cargar `.env` con `python-dotenv` (o nuestro fallback).\n"
            "- Patrón `client = get_influx_client()` con el helper del repo.\n"
            "- Cómo distinguir modo offline (mock) y online (real).\n"
            "- Smoke query Flux mínima de salud.\n"
            "- Por qué nunca commitear el `.env`.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Cualquier notebook posterior asume que esta conexión funciona. Si "
            "estás en clase sin Influx levantado, declara `INFLUX_OFFLINE=true` y los "
            "notebooks `needs-stack` mostrarán datos mockeados.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "El cliente que usaremos es **idéntico** al que usará CENTINELA+ contra "
            "`simarro-prod`. La única diferencia entre desarrollo y producción es la "
            "URL y el token. Esto es el corazón de la regla *cambio de credenciales, "
            "no reescritura*.",
        ),
        section(
            5,
            "Relación con Medallion",
            "Este notebook es la **puerta de entrada a la capa plata**. Sin esta "
            "conexión nadie puede leer ni escribir.",
        ),
        section(
            6,
            "Datos de entrada",
            "El `.env` del repo (`.env.example` como referencia). Variables esperadas: "
            "`INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET`.",
        ),
        setup_section(
            "Comprobamos que `INFLUXDB_URL` está cargado y que `python-dotenv` está "
            "disponible (si no, usamos el parser propio).",
        ),
        section(
            8,
            "Schema CAPTIA esperado",
            "El cliente solo se conecta al servidor; no escribe nada en este notebook. "
            "Las variables anteriores son del entorno, no del schema.",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Inspeccionamos las variables clave (sin imprimir el token completo).",
            """\
import os

def masked(value: str | None) -> str:
    if not value:
        return "<vacío>"
    return value[:4] + "*" * (max(0, len(value) - 4))

print("INFLUXDB_URL:", os.environ.get("INFLUXDB_URL", "<no definido>"))
print("INFLUXDB_ORG:", os.environ.get("INFLUXDB_ORG", "<no definido>"))
print("INFLUXDB_TOKEN:", masked(os.environ.get("INFLUXDB_TOKEN")))
print("OFFLINE MODE:", os.environ.get("INFLUX_OFFLINE", "false"))
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Intentamos abrir un cliente; si no se puede (sin servicios o sin "
            "`influxdb_client` instalado), mostramos cómo continuaríamos en modo offline.",
            """\
client = get_influx_client(allow_offline=True)
if client is None:
    print("Modo offline: trabajaremos con mocks de notebooks/_common/synthetic_mocks.py")
else:
    health = client.health()
    print("Conectado:", health.status, "—", health.message)
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "No aplica — este notebook prepara la herramienta, no la usa.",
        ),
        section(
            12,
            "Construcción de capa oro",
            "No aplica.",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Pintamos una pequeña gráfica de la disponibilidad de servicios para "
            "documentar visualmente nuestro estado de stack en clase.",
            """\
import os

def _is_truthy(env_var: str) -> bool:
    return os.environ.get(env_var, "").lower() in {"1", "true", "yes"}

estado = pd.Series(
    {
        "InfluxDB cliente": "ok" if client is not None else "offline",
        "python-dotenv": "instalado" if "dotenv" in dir() or os.environ.get("INFLUXDB_URL") else "fallback",
        "Modo OFFLINE explícito": "sí" if _is_truthy("INFLUX_OFFLINE") else "no",
    },
    name="estado",
)
estado.to_frame()
""",
        ),
        section(
            14,
            "Validaciones",
            "Comprobaciones mínimas que un alumno debería pasar antes de continuar.",
            """\
url = os.environ.get("INFLUXDB_URL")
token = os.environ.get("INFLUXDB_TOKEN")
assert url, "INFLUXDB_URL no definido — copiar .env.example a .env"
assert token, "INFLUXDB_TOKEN no definido — pedir credenciales a profesor"
assert "CHANGE_ME" not in token, "Sigue el placeholder de .env.example: regenerar con openssl"
print("Validaciones OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **`INFLUXDB_TOKEN=CHANGE_ME...`** sin reemplazar. Generar con "
            "`openssl rand -hex 32`.\n"
            "2. **Olvidar arrancar el stack** (`make demo` o `task up`).\n"
            "3. **Usar `localhost:8086` en lugar de `8087`** que es el puerto host.\n"
            "4. **No exportar las variables al kernel** — Jupyter Lab no recarga `.env` "
            "automáticamente al editarlo; reiniciar kernel.\n"
            "5. **Commitear `.env`**. Está en `.gitignore` por algo.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade un decorador `@requires_influx` que redirija a una función "
            "fallback con mocks si `client is None`.\n"
            "2. Implementa una función `ping(url)` que compruebe `/health` con `httpx`.\n"
            "3. Escribe la función `secret_okay(token)` que valide longitud mínima y "
            "ausencia de placeholders.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Para conectar a `simarro-prod` (producción CAPTIA): cambiar `INFLUXDB_URL` "
            "al endpoint LAN o Tailscale del IES, usar `edu-token-simarro` con permiso "
            "read-only, y dejar `INFLUX_OFFLINE` sin definir. El resto del código no "
            "cambia.",
        ),
        common_summary(
            next_notebook="01_case_A_pipeline_iot/01_explicacion_pipeline_centinela.ipynb",
            docs_link="docs/operations/environment.md",
            extra_bullets=(
                "La política de secretos del repo está en `docs/operations/environment.md`.",
            ),
        ),
    ]
    return emit(
        target=target,
        rel_path="00_project_overview/02_conexion_influxdb_y_variables_entorno.ipynb",
        title=title,
        case=CASE,
        layer="transversal",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_OVERVIEW,
    )


def build(target: Path) -> int:
    _nb_00_arquitectura(target)
    _nb_01_schema(target)
    _nb_02_conexion(target)
    return 3
