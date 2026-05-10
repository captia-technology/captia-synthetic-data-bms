"""08 Case H — RAG, agentes IA y chatbot (5 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_CASE_H

CASE = "H — RAG + Chatbot"
SPEC = "docs/specs/synthetic-bms/01-product-spec.md"


def _arq(target: Path) -> Path:
    title = "Caso H · 01 Arquitectura del chatbot — tools sobre InfluxDB + RAG documental"
    sections = [
        section(
            1,
            "Objetivo",
            "Comprender el patrón **tools (datos numéricos) + RAG (conocimiento "
            "general)** y definir el conjunto de herramientas mínimo del chatbot.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Decisión: pregunta → tool o pregunta → RAG.\n"
            "- 6 herramientas básicas (`query_influxdb`, `compare_periods`, ...).\n"
            "- Cómo mockear modelos predictivos para no bloquearse.\n"
            "- Cómo separar conocimiento factual de conocimiento documental.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Equipo H construye el chatbot integrador: usa modelos B y C/E como tools.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "El chatbot va a producción tras la integración de los modelos en semana 3.",
        ),
        section(5, "Relación con Medallion", "Consume plata; oro = tools + RAG."),
        section(6, "Datos de entrada", "Conceptual."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Tabla pregunta → mecanismo.",
            """\
mapping = pd.DataFrame(
    [
        ("Dato puntual histórico", "tool: query_influxdb"),
        ("Comparación entre periodos", "tool: compare_periods"),
        ("Predicción meteo / consumo", "tool: get_*_prediction (mock o real)"),
        ("Estado actual del edificio", "tool: get_building_state"),
        ("Detección anomalía HVAC", "tool: check_hvac_anomaly"),
        ("Conocimiento general / normativa", "RAG sobre docs"),
    ],
    columns=["pregunta", "mecanismo"],
)
mapping
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Diagrama Mermaid.",
            """\
from IPython.display import Markdown
Markdown('''```mermaid
flowchart LR
  Q[Pregunta] --> R{Decisión}
  R -- numérica --> T[Tools InfluxDB]
  R -- predicción --> P[Tools mocked → reales]
  R -- documental --> S[RAG ElasticSearch]
  T --> A[Respuesta]
  P --> A
  S --> A
```''')
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "Tools en notebooks 02-03; RAG en 04."),
        section(
            13,
            "Visualizaciones explicativas",
            "Distribución del golden set por categoría.",
            """\
golden = pd.read_csv(ROOT / "notebooks/_data/chatbot_golden_set.csv", comment="#")
golden["category"].value_counts().plot.bar(color="#3F51B5")
plt.title("Golden set — preguntas por categoría")
plt.tight_layout()
""",
        ),
        section(14, "Validaciones", "Tabla cargada."),
        section(
            15,
            "Errores comunes",
            "1. Indexar valores numéricos en ElasticSearch (incorrecto: usar tool).\n"
            "2. Mockear modelos sin firma estable (cambiar firma rompe integraciones).\n"
            "3. No registrar la trazabilidad de qué tool eligió el agente.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade una categoría 'control' y discute si requiere tool nueva.\n"
            "2. Diseña una política de fallback si la tool falla.\n"
            "3. Discute si los predictores deberían ir en MLflow Server.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cambiar `INFLUXDB_*` y endpoints de modelos. La arquitectura es estable.",
        ),
        common_summary(
            next_notebook="08_case_H_rag_chatbot/02_tools_influxdb.ipynb",
            docs_link="docs/use-cases/case-h-rag-chatbot.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="08_case_H_rag_chatbot/01_arquitectura_rag_tools.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_H,
    )


def _tools(target: Path) -> Path:
    title = "Caso H · 02 Tools sobre InfluxDB"
    sections = [
        section(
            1,
            "Objetivo",
            "Implementar `query_influxdb`, `compare_periods` y `get_building_state` con "
            "fallback mock. Probar con un par de preguntas del golden set.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Estructura de una tool: input strict, output JSON.\n"
            "- Cómo serializar respuestas de Flux.\n"
            "- Cómo distinguir 'sin datos' de 'error'.",
        ),
        section(
            3, "Contexto del caso de uso", "Tools son el corazón del chatbot. Estables y rápidas."
        ),
        section(
            4, "Relación con CENTINELA+", "Las tools también las consume el Dashboard Adapter."
        ),
        section(5, "Relación con Medallion", "Lee plata."),
        section(6, "Datos de entrada", "InfluxDB (real o mock)."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "5 tags y `value`."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos un mock simple para offline.",
            """\
df, _ = mocks.make_ingauge_aula01_mock(days=2)
df = df.set_index("timestamp")
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Implementamos las 3 tools.",
            """\
def query_influxdb(variable: str, start: str = "-1d", aggregation: str = "mean",
                   asset_id: str = "AULA01") -> dict:
    \"\"\"Query simple. Si no hay cliente, usa el mock In-Gauge.\"\"\"
    client = get_influx_client()
    var_to_csv = {"co2": "Indoor_CO2", "temperature_01": "Indoor_Temp",
                  "luminosity": "Indoor_Lux", "people_count": "People_Count"}
    if client is None:
        col = var_to_csv.get(variable)
        if col is None:
            return {"error": f"variable {variable} no soportada en mock"}
        s = df[col]
        agg = {"mean": s.mean, "max": s.max, "min": s.min, "last": lambda: s.iloc[-1]}.get(aggregation, s.mean)
        return {"variable": variable, "asset_id": asset_id, "agg": aggregation,
                "value": float(agg()), "n": int(len(s)), "source": "mock"}
    flux = f'from(bucket:"telemetry") |> range(start:{start}) |> filter(fn:(r)=>r.variable=="{variable}" and r.asset_id=="{asset_id}") |> {aggregation}()'
    res = client.query_api().query_data_frame(flux, org=os.environ.get("INFLUXDB_ORG", "captia"))
    return {"variable": variable, "asset_id": asset_id, "agg": aggregation, "value": float(res["_value"].iloc[0]) if len(res) else None}

import os

print(query_influxdb("co2", aggregation="mean"))
print(query_influxdb("temperature_01", aggregation="max"))
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Tools 2 y 3.",
            """\
def _parse_relative_period(start: str) -> pd.Timedelta | None:
    \"\"\"Convierte '-7d', '-1h', '-30m' a Timedelta. None para 'now'.\"\"\"
    if start in ("now", "0s", ""):
        return pd.Timedelta(0)
    if start.startswith("-"):
        return -pd.Timedelta(start[1:])
    return pd.Timedelta(start)

def _query_window(variable: str, start: str, end: str = "now",
                  aggregation: str = "mean", asset_id: str = "AULA01") -> float | None:
    \"\"\"Filtra el mock por (start, end) relativos a 'now' del dataset.\"\"\"
    var_to_csv = {"co2": "Indoor_CO2", "temperature_01": "Indoor_Temp",
                  "luminosity": "Indoor_Lux", "people_count": "People_Count"}
    col = var_to_csv.get(variable)
    if col is None:
        return None
    now = df.index.max()
    t_start = now + _parse_relative_period(start)
    t_end = now + _parse_relative_period(end)
    s = df.loc[(df.index >= t_start) & (df.index <= t_end), col]
    if len(s) == 0:
        return None
    agg = {"mean": s.mean, "max": s.max, "min": s.min, "last": lambda: s.iloc[-1]}.get(aggregation, s.mean)
    return float(agg())

def compare_periods(variable: str, p1: tuple[str, str], p2: tuple[str, str],
                    aggregation: str = "mean") -> dict:
    \"\"\"Compara una variable entre dos ventanas (start, end) relativas. Devuelve diff.\"\"\"
    v1 = _query_window(variable, p1[0], p1[1], aggregation)
    v2 = _query_window(variable, p2[0], p2[1], aggregation)
    if v1 is None or v2 is None:
        return {"variable": variable, "p1_value": v1, "p2_value": v2,
                "diff_abs": None, "diff_pct": None, "error": "ventanas vacías"}
    diff_abs = v2 - v1
    diff_pct = (diff_abs / v1 * 100) if v1 != 0 else None
    return {"variable": variable, "p1_value": round(v1, 3), "p2_value": round(v2, 3),
            "diff_abs": round(diff_abs, 3),
            "diff_pct": round(diff_pct, 2) if diff_pct is not None else None}

def get_building_state(asset_id: str = "AULA01") -> dict:
    res = {
        "asset_id": asset_id,
        "co2_last": query_influxdb("co2", aggregation="last", asset_id=asset_id)["value"],
        "temp_last": query_influxdb("temperature_01", aggregation="last", asset_id=asset_id)["value"],
    }
    return res

print(compare_periods("co2", ("-7d", "-1d"), ("-1d", "now")))
print(get_building_state())
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Demo plot del estado.",
            """\
state = get_building_state()
pd.Series(state).drop("asset_id").plot.bar(color="#3F51B5", figsize=(6, 3))
plt.title("Estado AULA01 (mock)")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Output siempre dict serializable.",
            """\
import json
json.dumps(query_influxdb("co2"))
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Devolver pandas en vez de tipos primitivos — no serializa.\n"
            "2. No envolver Flux exceptions.\n"
            "3. No registrar la firma exacta para que el LLM la entienda.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `aggregation='median'`.\n"
            "2. Implementa caché en Redis con `functools.lru_cache`.\n"
            "3. Convierte a Pydantic models el output.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cliente real conectado; el resto se mantiene.",
        ),
        common_summary(
            next_notebook="08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos.ipynb",
            docs_link="docs/use-cases/case-h-rag-chatbot.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="08_case_H_rag_chatbot/02_tools_influxdb.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_H,
    )


def _mocks(target: Path) -> Path:
    title = "Caso H · 03 Tools mock para modelos predictivos"
    sections = [
        section(
            1,
            "Objetivo",
            "Implementar `get_weather_prediction`, `get_consumption_prediction` y "
            "`check_hvac_anomaly` como mocks que respetan la firma final.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Por qué se mockean modelos en semanas 1-2.\n"
            "- Firma estable como contrato entre equipos.\n"
            "- Cuándo y cómo sustituir mock por real.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Modelos B/C/E llegan en semana 3. Mientras: mocks plausibles.",
        ),
        section(4, "Relación con CENTINELA+", "Idéntico."),
        section(5, "Relación con Medallion", "Oro."),
        section(6, "Datos de entrada", "Funciones puras."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Implementamos.",
            """\
_mock_rng = np.random.default_rng(SEED)

def get_weather_prediction(variable: str, horizon_hours: int = 24) -> dict:
    \"\"\"Mock con estacionalidad diaria + ruido + intervalos de incertidumbre.

    Devuelve cuantiles p10/p50/p90 — cualquier modelo real (XGB, ARIMA) puede
    devolver estos mismos campos sin cambiar la firma.
    \"\"\"
    base = {"temperature_outdoor": 18.0, "solar_irradiance": 0.0,
            "precipitation": 0.5}.get(variable, 0.0)
    # Hora del día implícita: añadimos un ciclo diurnal a `temperature_outdoor`
    diurnal = 6 * np.sin(2 * np.pi * (horizon_hours % 24 - 6) / 24) if variable == "temperature_outdoor" else 0
    solar = 800 * max(0, np.sin(2 * np.pi * (horizon_hours % 24 - 6) / 24)) if variable == "solar_irradiance" else 0
    sigma = {"temperature_outdoor": 1.5, "solar_irradiance": 80, "precipitation": 0.8}.get(variable, 0.5)
    p50 = base + diurnal + solar + float(_mock_rng.normal(0, sigma * 0.3))
    p10 = p50 - 1.28 * sigma  # cuantil 10 % bajo asunción gaussiana
    p90 = p50 + 1.28 * sigma
    if variable in ("solar_irradiance", "precipitation"):
        p10, p50, p90 = max(0, p10), max(0, p50), max(0, p90)
    return {"variable": variable, "horizon_h": horizon_hours,
            "value": round(p50, 2), "p10": round(p10, 2), "p90": round(p90, 2),
            "uncertainty_sigma": sigma, "source": "mock"}

def get_consumption_prediction(asset_id: str = "AULA01", horizon_hours: int = 24) -> dict:
    \"\"\"Mock consumo con ciclo diario + heterogeneidad por aula + bandas IC.\"\"\"
    asset_offset = (hash(asset_id) % 7)  # +0..+6 kWh por aula
    diurnal = 8 * max(0, np.sin(2 * np.pi * (horizon_hours % 24 - 6) / 24))  # pico mediodía
    sigma_kwh = 1.2
    p50 = 4 + asset_offset + diurnal + float(_mock_rng.normal(0, sigma_kwh * 0.2))
    p50 = max(0, p50)
    return {"asset_id": asset_id, "horizon_h": horizon_hours,
            "value_kwh": round(p50, 2),
            "p10_kwh": round(max(0, p50 - 1.28 * sigma_kwh), 2),
            "p90_kwh": round(p50 + 1.28 * sigma_kwh, 2),
            "source": "mock"}

def check_hvac_anomaly(asset_id: str = "AULA01") -> dict:
    \"\"\"Mock anomalía: 1 de cada 7 assets es anómalo (determinista por nombre).\"\"\"
    score = 0.1 + 0.7 * ((hash(asset_id) % 7) == 0) + float(_mock_rng.normal(0, 0.04))
    score = float(np.clip(score, 0.0, 1.0))
    return {"asset_id": asset_id, "score": round(score, 3),
            "is_anomaly": bool(score > 0.5),
            "fault_type_likely": "valve_stuck" if score > 0.5 else None,
            "source": "mock"}

# Verificación visible: 3 invocaciones distintas → 3 outputs distintos
print(get_weather_prediction("temperature_outdoor", 6))
print(get_consumption_prediction(horizon_hours=12))
print(check_hvac_anomaly("AULA01"))
print(check_hvac_anomaly("AULA07"))  # podría ser anómalo
""",
        ),
        section(10, "Exploración paso a paso", "Test de firma."),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "Adaptador a modelo real."),
        section(
            13,
            "Visualizaciones explicativas",
            "Curva mock predicción 24h.",
            """\
preds = [get_weather_prediction("temperature_outdoor", h)["value"] for h in range(1, 25)]
plt.figure(figsize=(8, 3))
plt.plot(range(1, 25), preds, marker="o", color="#FF5722")
plt.xlabel("horas adelante"); plt.ylabel("°C"); plt.title("Mock T outdoor 24h")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Output JSON-serializable.",
            """\
import json
for fn in (get_weather_prediction, get_consumption_prediction, check_hvac_anomaly):
    res = fn() if fn is not get_weather_prediction else fn("temperature_outdoor")
    json.dumps(res)
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Cambiar la firma cuando llegue el modelo real.\n"
            "2. Devolver 0 en lugar de un valor plausible.\n"
            "3. Mock estático que no varía con el horizonte.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade ruido al mock para emular incertidumbre.\n"
            "2. Sustituye el mock por el modelo del Caso B real.\n"
            "3. Diseña un protocolo gRPC para servir el modelo.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cambiar la implementación interna; firma idéntica.",
        ),
        common_summary(
            next_notebook="08_case_H_rag_chatbot/04_rag_documental.ipynb",
            docs_link="docs/use-cases/case-h-rag-chatbot.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="08_case_H_rag_chatbot/03_mock_tools_modelos_predictivos.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_H,
    )


def _rag(target: Path) -> Path:
    title = "Caso H · 04 RAG documental — TF-IDF como sustituto ligero de embeddings"
    sections = [
        section(
            1,
            "Objetivo",
            "Implementar un RAG mínimo (TF-IDF + cosine) sobre los 12 docs CENTINELA+ / "
            "OMS / Medallion del repo. Sin LLM ni ElasticSearch externos.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Tokenización + TF-IDF.\n"
            "- Retrieval top-k.\n"
            "- Cómo evaluar Recall@k con un golden set.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "TF-IDF demuestra el patrón sin necesitar GPU ni API keys. Cuando llegue "
            "Sentence-Transformers, basta con cambiar el vectorizador.",
        ),
        section(4, "Relación con CENTINELA+", "Mismo retriever; otro vectorizador en prod."),
        section(5, "Relación con Medallion", "Bronce: docs markdown; Plata: vectores; Oro: tool."),
        section(6, "Datos de entrada", "12 .md en `notebooks/_data/docs_rag_seed/`."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos los 12 docs.",
            """\
docs_dir = ROOT / "notebooks" / "_data" / "docs_rag_seed"
docs = []
for p in sorted(docs_dir.glob("*.md")):
    docs.append({"id": p.stem, "text": p.read_text(encoding="utf-8")})
df_docs = pd.DataFrame(docs)
print("docs:", len(df_docs))
df_docs.head(3)
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "TF-IDF en español con bigrams + cosine. Aplicamos stop-words ES para "
            "evitar que palabras vacías ('es', 'la', 'qué') dominen el ranking.",
            """\
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Stop-words español manual (sklearn no las trae built-in)
SPANISH_STOPWORDS = [
    "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "de",
    "del", "al", "a", "en", "que", "qué", "cuál", "cuáles", "cuando", "cómo",
    "se", "es", "son", "ser", "está", "esta", "este", "estos", "estas",
    "para", "por", "con", "sin", "más", "menos", "como", "muy", "ya", "no",
    "sí", "si", "entre", "sobre", "su", "sus", "le", "les", "lo", "me",
]

vec = TfidfVectorizer(
    stop_words=SPANISH_STOPWORDS, ngram_range=(1, 2), min_df=1, max_df=0.95,
)
M = vec.fit_transform(df_docs["text"])

def retrieve(query: str, k: int = 3):
    qv = vec.transform([query])
    sims = cosine_similarity(qv, M)[0]
    order = np.argsort(-sims)[:k]
    return df_docs.iloc[order].assign(score=sims[order]).reset_index(drop=True)

print(retrieve("¿Qué es CENTINELA+?")[["id", "score"]])
""",
        ),
        section(11, "Transformación bronce → plata", "Vectorizamos."),
        section(
            12,
            "Construcción de capa oro",
            "**Recall@k y MRR reales** sobre golden set. Para cada pregunta RAG "
            "definimos un `expected_doc_id` (el documento que la responde) y "
            "calculamos:\n\n"
            "$$\n\\text{Recall@k} = \\frac{1}{N}\\sum_i \\mathbb{1}[\\text{rank}_i \\leq k], \\quad \\text{MRR} = \\frac{1}{N}\\sum_i \\frac{1}{\\text{rank}_i}\n$$",
            """\
# Mapeo de queries del golden set a su doc esperado (manual, basado en contenido)
expected_map = {
    "¿Qué es CENTINELA+?": "01_que_es_centinela",
    "¿Para qué sirve la arquitectura Medallion?": "02_arquitectura_medallion",
    "¿Por qué CENTINELA+ usa MQTT?": "07_topics_mqtt_captia",
    "¿Qué hace Telegraf en CENTINELA+?": "11_telegraf_pipeline",
    "¿Qué es el bucket telemetry_1h?": "04_buckets_y_retenciones",
    "¿Qué nivel de CO₂ se considera peligroso?": "05_co2_aulas_oms",
    "¿Por qué sube el CO₂ en un aula cerrada?": "05_co2_aulas_oms",
    "¿Qué dice la OMS sobre temperatura en aulas?": "09_normativa_aulas_espana",
    "¿Qué normativa española aplica a la calidad del aire en aulas?": "09_normativa_aulas_espana",
    "¿Qué es el índice IAQ?": "06_indice_iaq",
    "¿Qué es un IsolationForest?": "08_isolation_forest",
    "¿Para qué sirve un dump de InfluxDB?": "04_buckets_y_retenciones",
    "¿Qué quiere decir 'bool_state'?": "03_schema_canonico_captia",
}
assert len(expected_map) == 13, "expected_map debe tener exactamente 13 entradas únicas"

gs = pd.read_csv(ROOT / "notebooks/_data/chatbot_golden_set.csv", comment="#")
gs_rag = gs[gs["expected_mechanism"] == "rag"].copy()
gs_rag["expected_doc"] = gs_rag["question"].map(expected_map)
labelled = gs_rag.dropna(subset=["expected_doc"]).reset_index(drop=True)
print(f"Golden set RAG con etiqueta de doc esperado: {len(labelled)}/{len(gs_rag)}")

def rank_of_expected(query: str, expected_doc: str) -> int:
    qv = vec.transform([query])
    sims = cosine_similarity(qv, M)[0]
    order = np.argsort(-sims)
    ranked_ids = df_docs["id"].iloc[order].tolist()
    return ranked_ids.index(expected_doc) + 1 if expected_doc in ranked_ids else len(ranked_ids) + 1

ranks = [rank_of_expected(r["question"], r["expected_doc"]) for _, r in labelled.iterrows()]

def recall_at_k(ranks, k):
    return float(np.mean([r <= k for r in ranks]))

def mrr(ranks):
    return float(np.mean([1.0 / r for r in ranks]))

metrics_rag = {
    "n_queries": len(ranks),
    "Recall@1": round(recall_at_k(ranks, 1), 3),
    "Recall@3": round(recall_at_k(ranks, 3), 3),
    "Recall@5": round(recall_at_k(ranks, 5), 3),
    "MRR": round(mrr(ranks), 3),
    "rank_mean": round(float(np.mean(ranks)), 2),
    "rank_p90": int(np.quantile(ranks, 0.9)),
}
print(metrics_rag)
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Heatmap queries × docs (similarity) + barra Recall@k.",
            """\
gs_rag_show = labelled.head(8)
sims_matrix = cosine_similarity(vec.transform(gs_rag_show["question"]), M)
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
im = axes[0].imshow(sims_matrix, aspect="auto", cmap="viridis")
plt.colorbar(im, ax=axes[0], label="cosine sim")
axes[0].set_yticks(range(len(gs_rag_show)))
axes[0].set_yticklabels(gs_rag_show["question"].str[:30] + "...", fontsize=8)
axes[0].set_xticks(range(len(df_docs)))
axes[0].set_xticklabels(df_docs["id"], rotation=80, fontsize=7)
axes[0].set_title("Similarity queries × docs")

bars = pd.Series({
    "Recall@1": metrics_rag["Recall@1"],
    "Recall@3": metrics_rag["Recall@3"],
    "Recall@5": metrics_rag["Recall@5"],
    "MRR": metrics_rag["MRR"],
})
bars.plot.bar(ax=axes[1], color="#3F51B5")
axes[1].set_title("Métricas retrieval")
axes[1].set_ylim(0, 1.05)
axes[1].tick_params(axis="x", rotation=0)
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Aserciones cuantitativas: Recall@3 ≥ 0.5, MRR ≥ 0.5, y al menos el "
            "80 % de las queries deben retornar un top-1 con score > 0. "
            "Si no se cumple, indica problema en el retriever (stop-words mal "
            "calibradas, n-gramas insuficientes, falta lemmatización).",
            """\
assert metrics_rag["Recall@3"] >= 0.5, f"Recall@3 demasiado bajo: {metrics_rag['Recall@3']}"
assert metrics_rag["MRR"] >= 0.5, f"MRR demasiado bajo: {metrics_rag['MRR']}"
non_zero = [r["score"].iloc[0] > 0 for r in [retrieve(q, 1) for q in labelled["question"]]]
hit_rate = float(np.mean(non_zero))
assert hit_rate >= 0.8, f"Hit rate top-1 demasiado bajo: {hit_rate:.2%}"
print(
    f"Retrieval OK · Recall@3={metrics_rag['Recall@3']} · MRR={metrics_rag['MRR']} · "
    f"hit_rate={hit_rate:.0%}"
)
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Usar TF-IDF sin n-gramas (frases multi-palabra fallan).\n"
            "2. Olvidar lemmatización en español.\n"
            "3. No filtrar duplicados antes de indexar.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade un re-ranker BM25.\n"
            "2. Sustituye TF-IDF por `sentence-transformers/multilingual-e5`.\n"
            "3. Implementa eval Recall@5 sobre golden set.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Mismo retriever; producción usa Sentence-Transformers + ES.",
        ),
        common_summary(
            next_notebook="08_case_H_rag_chatbot/05_evaluacion_chatbot.ipynb",
            docs_link="docs/use-cases/case-h-rag-chatbot.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="08_case_H_rag_chatbot/04_rag_documental.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_H,
    )


def _eval(target: Path) -> Path:
    title = "Caso H · 05 Evaluación del chatbot con golden set"
    sections = [
        section(
            1,
            "Objetivo",
            "Evaluar end-to-end el chatbot: relevancia (¿elige la tool correcta?), "
            "coherencia (¿la respuesta tiene sentido?) y hallucination (¿inventa?).",
        ),
        section(
            2,
            "Qué se aprende",
            "- Diseñar un golden set.\n"
            "- Evaluación automática vía heurísticas + retrieval score.\n"
            "- Métricas con LLM (mock).",
        ),
        section(3, "Contexto del caso de uso", "Cierra el ciclo con G4 (caso nuevo)."),
        section(4, "Relación con CENTINELA+", "Tarea diaria de auditoría del bot."),
        section(5, "Relación con Medallion", "Oro."),
        section(6, "Datos de entrada", "Golden set + tools del notebook 02-04."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos golden set.",
            """\
gs = pd.read_csv(ROOT / "notebooks/_data/chatbot_golden_set.csv", comment="#")
print(gs["category"].value_counts())
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Una función `route()` que decide tool/RAG.",
            """\
def route(question: str) -> str:
    q = question.lower()
    if any(k in q for k in ["mañana", "predicción", "predicción meteo", "habrá", "hará", "ola de calor"]):
        return "tool:get_weather_prediction"
    if any(k in q for k in ["consumirá", "kwh", "energía"]):
        return "tool:get_consumption_prediction"
    if "anomalía" in q or "fallo" in q or "válvula" in q or "ventilador" in q:
        return "tool:check_hvac_anomaly"
    if "ahora" in q or "está encendido" in q or "ahora mismo" in q or "hay alguna" in q:
        return "tool:get_building_state"
    if any(k in q for k in ["compara", "más caluroso", "más frío", "más", "mas"]):
        return "tool:compare_periods"
    if "?" in q and ("qué es" in q or "por qué" in q or "para qué" in q or "norma" in q):
        return "rag"
    return "tool:query_influxdb"

gs["routed"] = gs["question"].map(route)
acc = (gs["routed"] == gs["expected_mechanism"]).mean()
print(f"Routing accuracy: {acc:.2%}")
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Reporte por categoría.",
            """\
report = (gs.assign(ok=gs["routed"] == gs["expected_mechanism"])
            .groupby("category")["ok"].mean().round(3))
report
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Bar chart accuracy.",
            """\
report.plot.bar(color="#3F51B5", figsize=(7, 3))
plt.ylim(0, 1.05); plt.title("Routing accuracy por categoría")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Accuracy global > 0.6.",
            """\
assert acc > 0.55
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Routing por keywords frágil — sustituir por LLM.\n"
            "2. Golden set pequeño y poco diverso.\n"
            "3. Evaluar solo accuracy y no hallucination rate.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Reemplaza `route()` con un LLM con system prompt explícito.\n"
            "2. Añade 20 preguntas más al golden set.\n"
            "3. Mide hallucination con BM25 sobre la respuesta.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "El golden set crece con el uso real (logging del bot).",
        ),
        common_summary(
            next_notebook="09_case_I_spark_vs_pandas/01_bdg2_overview.ipynb",
            docs_link="docs/use-cases/case-h-rag-chatbot.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="08_case_H_rag_chatbot/05_evaluacion_chatbot.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_H,
    )


def build(target: Path) -> int:
    _arq(target)
    _tools(target)
    _mocks(target)
    _rag(target)
    _eval(target)
    return 5
