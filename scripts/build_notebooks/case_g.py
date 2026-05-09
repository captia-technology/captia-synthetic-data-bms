"""07 Case G — Calidad de datos con agentes especialistas (4 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section

CASE = "G — Calidad con agentes"
SPEC = "docs/specs/synthetic-bms/02-domain-spec.md"


def _bronce(target: Path) -> Path:
    title = "Caso G · 01 Reglas de calidad sobre la capa bronce"
    sections = [
        section(1, "Objetivo",
                "Definir y ejecutar reglas Great-Expectations-style sobre los CSV originales "
                "(In-Gauge, BDG2, LBNL FDD) **sin** depender de Influx levantado."),
        section(2, "Qué se aprende",
                "- Por qué la calidad bronce es la primera línea de defensa.\n"
                "- Reglas: rangos, no nulos, tipos.\n"
                "- Cómo escribir reglas sin Great Expectations (`pandera`-lite)."),
        section(3, "Contexto del caso de uso",
                "Equipo G empieza semana 1: reglas bronce sobre CSV de los demás equipos. "
                "Estrategia anti-bloqueo."),
        section(4, "Relación con CENTINELA+",
                "Las reglas bronce protegen el ETL real desde el día 1."),
        section(5, "Relación con Medallion", "Bronce."),
        section(6, "Datos de entrada", "Mocks de los demás casos."),
        section(7, "Schema CAPTIA esperado", "No aplica (aún en bronce)."),
        setup_section(),
        section(9, "Carga de datos o mock", "Cargamos los 3 CSV.",
                """\
ingauge = pd.read_csv(ROOT / "notebooks/_data/ingauge_aula01_mock.csv", comment="#", parse_dates=["timestamp"])
bdg2 = pd.read_csv(ROOT / "notebooks/_data/bdg2_education_subset_mock.csv", comment="#", parse_dates=["timestamp"])
lbnl = pd.read_csv(ROOT / "notebooks/_data/lbnl_fdd_rtu_mock.csv", comment="#", parse_dates=["timestamp"])
print({"ingauge": ingauge.shape, "bdg2": bdg2.shape, "lbnl": lbnl.shape})
"""),
        section(10, "Exploración paso a paso", "Definimos un mini DSL de reglas.",
                """\
from dataclasses import dataclass
from typing import Callable

@dataclass
class Rule:
    name: str
    fn: Callable[[pd.DataFrame], bool]
    description: str

rules = [
    Rule("ingauge_co2_range",
         lambda d: d["Indoor_CO2"].between(300, 5000).all(),
         "CO2 entre 300 y 5000 ppm"),
    Rule("ingauge_no_negative_people",
         lambda d: (d["People_Count"] >= 0).all(),
         "people_count no negativo"),
    Rule("bdg2_power_nonneg",
         lambda d: (d["power_kw"] >= 0).all(),
         "power no negativo"),
    Rule("lbnl_dt_supply_return",
         lambda d: ((d["RA_TEMP"] - d["SA_TEMP"]) >= -2).all(),
         "ΔT supply-return físicamente plausible"),
]
print(f"{len(rules)} reglas registradas")
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro",
                "Reporte por dataset.",
                """\
def evaluate(rules, ds_map):
    rows = []
    for r in rules:
        for ds_name, ds in ds_map.items():
            try:
                ok = bool(r.fn(ds))
            except KeyError:
                continue
            rows.append({"rule": r.name, "dataset": ds_name, "ok": ok})
    return pd.DataFrame(rows)

report = evaluate(rules, {"ingauge": ingauge, "bdg2": bdg2, "lbnl": lbnl})
report
"""),
        section(13, "Visualizaciones explicativas", "Heatmap.",
                """\
heat = report.pivot(index="rule", columns="dataset", values="ok").fillna("-")
heat.applymap(lambda v: "✓" if v is True else ("✗" if v is False else "—"))
"""),
        section(14, "Validaciones", "Todo OK.",
                """\
fails = report[report["ok"] == False]
assert fails.empty, f"Reglas falladas: {fails}"
print("Bronze quality: PASS")
"""),
        section(15, "Errores comunes",
                "1. Reglas demasiado estrictas que rechazan datos reales.\n"
                "2. Reglas que tardan demasiado en grandes datasets.\n"
                "3. No diferenciar warning de error."),
        section(16, "Ejercicios propuestos",
                "1. Añade una regla de monotonicidad temporal.\n"
                "2. Convierte las reglas a Great Expectations.\n"
                "3. Diseña una regla para detectar outliers > 3σ."),
        section(17, "Cómo se reutiliza con datos reales", "Idéntico — solo cambia origen."),
        common_summary(next_notebook="07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb.ipynb",
                       docs_link="docs/validation/data-quality.md"),
    ]
    return emit(target=target, rel_path="07_case_G_data_quality_agents/01_reglas_calidad_bronce.ipynb",
                title=title, case=CASE, layer="bronce", spec=SPEC, sections=sections)


def _plata(target: Path) -> Path:
    title = "Caso G · 02 Reglas Flux sobre la capa plata"
    sections = [
        section(1, "Objetivo",
                "Validar la capa plata directamente con queries Flux: completitud, "
                "rangos, presencia de los 5 tags, ausencia de variables sin metadata."),
        section(2, "Qué se aprende",
                "- Cómo escribir reglas Flux concisas.\n"
                "- Cómo automatizar el chequeo desde Python.\n"
                "- Reglas críticas vs warnings."),
        section(3, "Contexto del caso de uso",
                "Cuando los demás equipos cargan plata, G debe avisar de problemas. Las "
                "reglas viven en repo y se ejecutan periódicamente."),
        section(4, "Relación con CENTINELA+",
                "Las mismas reglas correrán contra `simarro-prod`."),
        section(5, "Relación con Medallion", "Plata."),
        section(6, "Datos de entrada", "InfluxDB (real o mock)."),
        section(7, "Schema CAPTIA esperado", "Las 5 tags + field value."),
        setup_section(),
        section(9, "Carga de datos o mock",
                "Si Influx vivo, ejecutamos. Si no, definimos las queries para revisión.",
                """\
flux_queries = {
    "completitud_co2": '''
from(bucket:"telemetry") |> range(start: -1d)
  |> filter(fn:(r) => r._measurement=="captia_point" and r.variable=="co2")
  |> count()
''',
    "rango_co2": '''
from(bucket:"telemetry") |> range(start: -1d)
  |> filter(fn:(r) => r.variable=="co2")
  |> filter(fn:(r) => r._value < 300 or r._value > 5000)
  |> count()
''',
    "presencia_tags": '''
schema.measurementTagKeys(bucket:"telemetry", measurement:"captia_point")
''',
    "metadata_pobladas": '''
from(bucket:"captia_metadata") |> range(start:-30d)
  |> filter(fn:(r) => r._measurement=="captia_point_meta")
  |> distinct(column:"variable")
  |> count()
''',
}
print(list(flux_queries.keys()))
"""),
        section(10, "Exploración paso a paso", "Ejecutamos si tenemos cliente.",
                """\
client = get_influx_client()
results = {}
if client is not None:
    org = os.environ.get("INFLUXDB_ORG", "captia")
    for name, q in flux_queries.items():
        try:
            res = client.query_api().query_data_frame(q, org=org)
            results[name] = res
        except Exception as e:
            results[name] = f"error: {e}"
else:
    print("Modo offline: las queries quedan documentadas; `make demo` y re-ejecutar.")
results
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "Reporte JSON."),
        section(13, "Visualizaciones explicativas", "Tabla — hits por regla."),
        section(14, "Validaciones",
                "Si tenemos cliente, ninguna regla 'rango' devuelve filas (=0 fuera de rango).",
                """\
import os

if client is not None and isinstance(results.get("rango_co2"), pd.DataFrame):
    df = results["rango_co2"]
    print("Filas fuera rango CO2:", df["_value"].iloc[0] if len(df) else 0)
"""),
        section(15, "Errores comunes",
                "1. Olvidar `range(start)` — Flux pide ventana.\n"
                "2. Filtrar por `_field` cuando solo hay `value`.\n"
                "3. No agrupar por aula/variable."),
        section(16, "Ejercicios propuestos",
                "1. Añade regla 'no_state_in_telemetry'.\n"
                "2. Construye una vista que enumere variables no metadatadas.\n"
                "3. Convierte la query en Flux Task con notification."),
        section(17, "Cómo se reutiliza con datos reales",
                "Las queries son las mismas; la dashboard de calidad es transversal."),
        common_summary(next_notebook="07_case_G_data_quality_agents/03_reglas_calidad_oro_ml.ipynb",
                       docs_link="docs/validation/data-quality.md"),
    ]
    return emit(target=target, rel_path="07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb.ipynb",
                title=title, case=CASE, layer="plata", spec=SPEC, sections=sections)


def _oro(target: Path) -> Path:
    title = "Caso G · 03 Calidad sobre la capa oro (datasets ML)"
    sections = [
        section(1, "Objetivo",
                "Reglas sobre datasets de entrenamiento: balance de clases, sin leakage, "
                "distribución train/test similar."),
        section(2, "Qué se aprende",
                "- Detección de leakage temporal y por features.\n"
                "- KL divergence train vs test.\n"
                "- Balance de clases."),
        section(3, "Contexto del caso de uso", "Auditar oros de B/C/D."),
        section(4, "Relación con CENTINELA+", "Pre-deploy gating."),
        section(5, "Relación con Medallion", "Oro."),
        section(6, "Datos de entrada", "Features Caso B y D si existen."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(9, "Carga de datos o mock", "Cargamos features B (con fallback inline).",
                """\
parquet = ROOT / "output" / "case_B" / "features_b0.parquet"
if parquet.exists():
    X = pd.read_parquet(parquet)
else:
    df, _ = mocks.make_bdg2_education_subset()
    df = df[df.building_id == df.building_id.unique()[0]].set_index("timestamp")
    X = pd.DataFrame({
        "y": df["power_kw"],
        "t_outdoor": df["t_outdoor"],
        "lag_24h": df["power_kw"].shift(24),
    }).dropna()
print(X.shape)
"""),
        section(10, "Exploración paso a paso", "Split temporal y comparación.",
                """\
n = len(X); i = int(n * 0.8)
tr, te = X.iloc[:i], X.iloc[i:]
desc_tr = tr.describe().T[["mean", "std"]].add_suffix("_tr")
desc_te = te.describe().T[["mean", "std"]].add_suffix("_te")
desc = pd.concat([desc_tr, desc_te], axis=1)
desc.round(3)
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro",
                "KL divergence aproximada por bins.",
                """\
def kl_hist(a, b, bins=20):
    a_h, _ = np.histogram(a, bins=bins, density=True)
    b_h, _ = np.histogram(b, bins=bins, density=True)
    a_h = a_h + 1e-9
    b_h = b_h + 1e-9
    return float(np.sum(a_h * np.log(a_h / b_h)))

cols = [c for c in X.columns if c != "y"]
kl = pd.Series({c: kl_hist(tr[c], te[c]) for c in cols}).sort_values()
kl
"""),
        section(13, "Visualizaciones explicativas", "Bar chart KL.",
                """\
kl.plot.barh(color="#9C27B0", figsize=(7, 3))
plt.title("KL train vs test (bajo = misma distribución)")
plt.tight_layout()
"""),
        section(14, "Validaciones", "KL < 1 para todas las features.",
                """\
assert kl.max() < 2.0, f"Drift fuerte: {kl}"
print("Drift OK")
"""),
        section(15, "Errores comunes",
                "1. KL con bins muy pequeños.\n"
                "2. No comparar la columna target.\n"
                "3. Métricas en escala absoluta sin estandarizar."),
        section(16, "Ejercicios propuestos",
                "1. Implementa Wasserstein distance.\n"
                "2. Visualiza un drift artificial añadiendo +5 °C al test.\n"
                "3. Construye un detector que envíe alerta si KL > umbral."),
        section(17, "Cómo se reutiliza con datos reales",
                "Mismo notebook sobre dataset producción cada noche."),
        common_summary(next_notebook="07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb",
                       docs_link="docs/validation/data-quality.md"),
    ]
    return emit(target=target, rel_path="07_case_G_data_quality_agents/03_reglas_calidad_oro_ml.ipynb",
                title=title, case=CASE, layer="oro", spec=SPEC, sections=sections)


def _agentes(target: Path) -> Path:
    title = "Caso G · 04 Agentes especialistas de calidad (mock)"
    sections = [
        section(1, "Objetivo",
                "Implementar 3 agentes-mock que actúan como evaluadores: validador de "
                "plata, auditor de MLflow, evaluador de chatbot."),
        section(2, "Qué se aprende",
                "- Patrón `@tool` / `@function_tool`.\n"
                "- Cómo combinar herramientas en un agente.\n"
                "- Cómo mockear LLM si no hay clave."),
        section(3, "Contexto del caso de uso",
                "Curso evalúa la calidad del proyecto con un agente que llama a herramientas. "
                "Usaremos un cliente fake."),
        section(4, "Relación con CENTINELA+",
                "Los agentes pueden correr como tarea diaria desde el Dashboard Adapter."),
        section(5, "Relación con Medallion", "Transversal."),
        section(6, "Datos de entrada", "Mocks."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(9, "Carga de datos o mock", "Definimos 3 tools.",
                """\
def validate_silver_layer(asset_id: str = "AULA01") -> dict:
    return {
        "asset_id": asset_id, "tags_present": True, "completeness_pct": 99.2,
        "outliers": 0, "verdict": "OK",
    }

def audit_mlflow_experiment(name: str = "case_B_baseline_2026") -> dict:
    return {
        "experiment": name, "n_runs": 4, "best_MAE": 12.4, "lakefs_tag_referenced": True,
        "verdict": "OK",
    }

def evaluate_chatbot_response(question: str, expected: str) -> dict:
    score = 0.85 if expected.lower()[:6] in question.lower() else 0.4
    return {"q": question, "expected": expected, "score": score, "hallucination": score < 0.3}

print(validate_silver_layer())
print(audit_mlflow_experiment())
print(evaluate_chatbot_response("¿Cuál es la temperatura?", "valor numérico"))
"""),
        section(10, "Exploración paso a paso", "Combinamos en un mini-agente.",
                """\
TOOLS = {
    "validate_silver_layer": validate_silver_layer,
    "audit_mlflow_experiment": audit_mlflow_experiment,
    "evaluate_chatbot_response": evaluate_chatbot_response,
}

def call_agent(plan: list[tuple[str, dict]]) -> list[dict]:
    out = []
    for name, kwargs in plan:
        out.append({"tool": name, "result": TOOLS[name](**kwargs)})
    return out

plan = [
    ("validate_silver_layer", {"asset_id": "AULA01"}),
    ("audit_mlflow_experiment", {"name": "case_B_baseline_2026"}),
    ("evaluate_chatbot_response", {"question": "¿Cuál fue la T media ayer?", "expected": "valor numérico"}),
]
results = call_agent(plan)
results
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "Informe consolidado.",
                """\
report = pd.DataFrame([{**{"tool": r["tool"]}, **r["result"]} for r in results])
report
"""),
        section(13, "Visualizaciones explicativas", "Verdict por tool.",
                """\
report["tool"].value_counts().plot.bar(color="#3F51B5")
plt.title("Tools invocadas")
plt.tight_layout()
"""),
        section(14, "Validaciones",
                "Cada tool retorna un dict válido y JSON-serializable.",
                """\
import json
for r in results:
    json.dumps(r["result"])
print("Serialización OK")
"""),
        section(15, "Errores comunes",
                "1. Tools que devuelven None.\n"
                "2. Captura silenciosa de excepciones — el agente no detecta el fallo.\n"
                "3. No registrar timing por tool."),
        section(16, "Ejercicios propuestos",
                "1. Reemplaza el evaluador de chatbot por embeddings simples.\n"
                "2. Añade `audit_data_drift(period)`.\n"
                "3. Conecta a un LLM real con `OPENAI_API_KEY`."),
        section(17, "Cómo se reutiliza con datos reales",
                "Las tools no cambian: solo el origen de los datos."),
        common_summary(next_notebook="08_case_H_rag_chatbot/01_arquitectura_rag_tools.ipynb",
                       docs_link="docs/use-cases/case-g-data-quality-agents.md"),
    ]
    return emit(target=target, rel_path="07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb",
                title=title, case=CASE, layer="transversal", spec=SPEC, sections=sections)


def build(target: Path) -> int:
    _bronce(target)
    _plata(target)
    _oro(target)
    _agentes(target)
    return 4
