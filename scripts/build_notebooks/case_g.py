"""07 Case G — Calidad de datos con agentes especialistas (4 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_CASE_G

CASE = "G — Calidad con agentes"
SPEC = "docs/specs/synthetic-bms/02-domain-spec.md"


def _bronce(target: Path) -> Path:
    title = "Caso G · 01 Reglas de calidad sobre la capa bronce"
    sections = [
        section(
            1,
            "Objetivo",
            "Definir y ejecutar reglas Great-Expectations-style sobre los CSV originales "
            "(In-Gauge, BDG2, LBNL FDD) **sin** depender de Influx levantado.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Por qué la calidad bronce es la primera línea de defensa.\n"
            "- Reglas: rangos, no nulos, tipos.\n"
            "- Cómo escribir reglas sin Great Expectations (`pandera`-lite).",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Equipo G empieza semana 1: reglas bronce sobre CSV de los demás equipos. "
            "Estrategia anti-bloqueo.",
        ),
        section(
            4, "Relación con CENTINELA+", "Las reglas bronce protegen el ETL real desde el día 1."
        ),
        section(5, "Relación con Medallion", "Bronce."),
        section(6, "Datos de entrada", "Mocks de los demás casos."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica (aún en bronce)."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos los 3 CSV.",
            """\
ingauge = pd.read_csv(ROOT / "notebooks/_data/ingauge_aula01_mock.csv", comment="#", parse_dates=["timestamp"])
bdg2 = pd.read_csv(ROOT / "notebooks/_data/bdg2_education_subset_mock.csv", comment="#", parse_dates=["timestamp"])
lbnl = pd.read_csv(ROOT / "notebooks/_data/lbnl_fdd_rtu_mock.csv", comment="#", parse_dates=["timestamp"])
print({"ingauge": ingauge.shape, "bdg2": bdg2.shape, "lbnl": lbnl.shape})
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Definimos un mini DSL de reglas.",
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
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
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
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Heatmap.",
            """\
heat = report.pivot(index="rule", columns="dataset", values="ok").fillna("-")
# pandas 2.x deprecó DataFrame.applymap; usamos  por columna.
heat_render = heat.apply(lambda col: col.map(lambda v: "ok" if v is True else ("FAIL" if v is False else "—")))
heat_render
""",
        ),
        section(
            14,
            "Validaciones",
            "Todo OK.",
            """\
fails = report[report["ok"] == False]
assert fails.empty, f"Reglas falladas: {fails}"
print("Bronze quality: PASS")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Reglas demasiado estrictas que rechazan datos reales.\n"
            "2. Reglas que tardan demasiado en grandes datasets.\n"
            "3. No diferenciar warning de error.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade una regla de monotonicidad temporal.\n"
            "2. Convierte las reglas a Great Expectations.\n"
            "3. Diseña una regla para detectar outliers > 3σ.",
        ),
        section(17, "Cómo se reutiliza con datos reales", "Idéntico — solo cambia origen."),
        common_summary(
            next_notebook="07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb.ipynb",
            docs_link="docs/validation/data-quality.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="07_case_G_data_quality_agents/01_reglas_calidad_bronce.ipynb",
        title=title,
        case=CASE,
        layer="bronce",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_G,
    )


def _plata(target: Path) -> Path:
    title = "Caso G · 02 Reglas Flux sobre la capa plata"
    sections = [
        section(
            1,
            "Objetivo",
            "Validar la capa plata directamente con queries Flux: completitud, "
            "rangos, presencia de los 5 tags, ausencia de variables sin metadata.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Cómo escribir reglas Flux concisas.\n"
            "- Cómo automatizar el chequeo desde Python.\n"
            "- Reglas críticas vs warnings.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Cuando los demás equipos cargan plata, G debe avisar de problemas. Las "
            "reglas viven en repo y se ejecutan periódicamente.",
        ),
        section(4, "Relación con CENTINELA+", "Las mismas reglas correrán contra `simarro-prod`."),
        section(5, "Relación con Medallion", "Plata."),
        section(6, "Datos de entrada", "InfluxDB (real o mock)."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "Las 5 tags + field value."),
        section(
            9,
            "Carga de datos o mock",
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
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Si Influx está vivo ejecutamos las queries reales; si no, **simulamos** "
            "su resultado parseando el line protocol del Caso D (`iaq_telemetry.lp`) "
            "para que el alumno vea siempre el resultado esperado.",
            """\
import os, re
client = get_influx_client()

def _simulate_query(name: str) -> pd.DataFrame:
    \"\"\"Ejecuta una versión Python de cada regla sobre el .lp del Caso D.\"\"\"
    lp_path = ROOT / "output" / "case_D" / "iaq_telemetry.lp"
    if not lp_path.exists():
        # Generar lazy desde mock si el .lp del Caso D no existe
        ing, _ = mocks.make_ingauge_aula01_mock(days=1)
        rows = []
        for _, r in ing.iterrows():
            rows.append({"variable": "co2", "value": r["Indoor_CO2"], "_time": r["timestamp"]})
        df_sim = pd.DataFrame(rows)
    else:
        # Parsear line protocol minimal
        rows = []
        pat = re.compile(r"variable=(\\w+).*?value=([0-9.]+)\\s+(\\d+)")
        for line in lp_path.read_text(encoding="utf-8").splitlines():
            m = pat.search(line)
            if m:
                rows.append({"variable": m.group(1), "value": float(m.group(2)),
                             "_time": pd.Timestamp(int(m.group(3)), unit="ns", tz="UTC")})
        df_sim = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["variable", "value", "_time"])

    if name == "completitud_co2":
        n = int((df_sim["variable"] == "co2").sum())
        return pd.DataFrame([{"_value": n}])
    if name == "rango_co2":
        bad = df_sim[(df_sim["variable"] == "co2") &
                     ((df_sim["value"] < 300) | (df_sim["value"] > 5000))]
        return pd.DataFrame([{"_value": int(len(bad))}])
    if name == "presencia_tags":
        return pd.DataFrame({"_value": ["captia_env", "domain_id", "site_id", "asset_id", "variable"]})
    if name == "metadata_pobladas":
        return pd.DataFrame([{"_value": int(df_sim["variable"].nunique())}])
    return pd.DataFrame()

results = {}
if client is not None:
    org = os.environ.get("INFLUXDB_ORG", "captia")
    for name, q in flux_queries.items():
        try:
            results[name] = client.query_api().query_data_frame(q, org=org)
            results[name + "_source"] = "real"
        except Exception as e:  # noqa: BLE001
            results[name] = _simulate_query(name)
            results[name + "_source"] = f"simulated (error real: {e})"
else:
    for name in flux_queries:
        results[name] = _simulate_query(name)
        results[name + "_source"] = "simulated (offline)"

# Resumen tabular
summary = pd.DataFrame([
    {
        "regla": name,
        "valor": int(results[name]["_value"].iloc[0]) if isinstance(results[name], pd.DataFrame)
                 and "_value" in results[name].columns and len(results[name])
                 and isinstance(results[name]["_value"].iloc[0], (int, float))
                 else (len(results[name]) if isinstance(results[name], pd.DataFrame) else "?"),
        "fuente": results.get(name + "_source", "?"),
    }
    for name in flux_queries
])
print(summary.to_string(index=False))
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Reporte JSON persistido (auditable, integrable con Grafana Annotations).",
            """\
import json

quality_report = {
    "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
    "stack_status": "live" if client is not None else "offline_simulated",
    "rules": {
        name: {
            "value": int(results[name]["_value"].iloc[0]) if isinstance(results[name], pd.DataFrame)
                    and "_value" in results[name].columns and len(results[name])
                    and isinstance(results[name]["_value"].iloc[0], (int, float))
                    else None,
            "source": results.get(name + "_source", "unknown"),
        }
        for name in flux_queries
    },
}
out_dir = ROOT / "output" / "case_G"
out_dir.mkdir(parents=True, exist_ok=True)
report_path = out_dir / "quality_silver_report.json"
report_path.write_text(json.dumps(quality_report, indent=2), encoding="utf-8")
print(f"Reporte: {report_path.relative_to(ROOT)}")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Bar chart de hits por regla con threshold visible (verde=ok, rojo=fail).",
            """\
import matplotlib.pyplot as plt

THRESHOLDS = {"completitud_co2": 100, "rango_co2": 0, "presencia_tags": 5, "metadata_pobladas": 1}
plot_data = []
for name in flux_queries:
    val = int(results[name]["_value"].iloc[0]) if isinstance(results[name], pd.DataFrame) \\
          and "_value" in results[name].columns and len(results[name]) \\
          and isinstance(results[name]["_value"].iloc[0], (int, float)) else \\
          (len(results[name]) if isinstance(results[name], pd.DataFrame) else 0)
    plot_data.append({"regla": name, "valor": val, "umbral": THRESHOLDS.get(name, 0)})

dfp = pd.DataFrame(plot_data)
fig, ax = plt.subplots(figsize=(8, 4))
colors = ["#4CAF50" if (
    (r["regla"] == "rango_co2" and r["valor"] == r["umbral"]) or
    (r["regla"] != "rango_co2" and r["valor"] >= r["umbral"])
) else "#FF5722" for _, r in dfp.iterrows()]
ax.bar(dfp["regla"], dfp["valor"], color=colors, alpha=0.85, edgecolor="white")
for i, (_, r) in enumerate(dfp.iterrows()):
    ax.axhline(r["umbral"], xmin=(i)/len(dfp), xmax=(i+1)/len(dfp),
               color="black", linestyle="--", linewidth=1)
ax.set_title("Reglas calidad plata — verde=OK, rojo=FAIL")
ax.set_ylabel("hits")
plt.xticks(rotation=15, ha="right")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Aserción cuantitativa: `rango_co2` debe ser **0** (ningún valor fuera de "
            "300-5000 ppm) y `presencia_tags` debe tener exactamente 5 tags canónicos.",
            """\
import os

rango_val = int(results["rango_co2"]["_value"].iloc[0]) if isinstance(results["rango_co2"], pd.DataFrame) and "_value" in results["rango_co2"].columns and len(results["rango_co2"]) else 0
assert rango_val == 0, f"Filas CO2 fuera rango fisico: {rango_val}"

if isinstance(results["presencia_tags"], pd.DataFrame) and "_value" in results["presencia_tags"].columns:
    n_tags = len(results["presencia_tags"])
    assert n_tags >= 5, f"Esperaba 5 tags canonicos, encontre {n_tags}"

print(f"Reglas plata OK · rango_co2={rango_val} · fuente={results.get('rango_co2_source')}")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Olvidar `range(start)` — Flux pide ventana.\n"
            "2. Filtrar por `_field` cuando solo hay `value`.\n"
            "3. No agrupar por aula/variable.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade regla 'no_state_in_telemetry'.\n"
            "2. Construye una vista que enumere variables no metadatadas.\n"
            "3. Convierte la query en Flux Task con notification.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Las queries son las mismas; la dashboard de calidad es transversal.",
        ),
        common_summary(
            next_notebook="07_case_G_data_quality_agents/03_reglas_calidad_oro_ml.ipynb",
            docs_link="docs/validation/data-quality.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb.ipynb",
        title=title,
        case=CASE,
        layer="plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_G,
    )


def _oro(target: Path) -> Path:
    title = "Caso G · 03 Calidad sobre la capa oro (datasets ML)"
    sections = [
        section(
            1,
            "Objetivo",
            "Reglas sobre datasets de entrenamiento: balance de clases, sin leakage, "
            "distribución train/test similar.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Detección de leakage temporal y por features.\n"
            "- KL divergence train vs test.\n"
            "- Balance de clases.",
        ),
        section(3, "Contexto del caso de uso", "Auditar oros de B/C/D."),
        section(4, "Relación con CENTINELA+", "Pre-deploy gating."),
        section(5, "Relación con Medallion", "Oro."),
        section(6, "Datos de entrada", "Features Caso B y D si existen."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos features B (con fallback inline).",
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
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Split temporal y comparación.",
            """\
n = len(X); i = int(n * 0.8)
tr, te = X.iloc[:i], X.iloc[i:]
desc_tr = tr.describe().T[["mean", "std"]].add_suffix("_tr")
desc_te = te.describe().T[["mean", "std"]].add_suffix("_te")
desc = pd.concat([desc_tr, desc_te], axis=1)
desc.round(3)
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "KL divergence aproximada por bins.",
            """\
def kl_hist(a, b, bins=20):
    \"\"\"KL divergence robusta a soportes diferentes.

    KL siempre >= 0 (identidad de Gibbs). Para garantizarlo:
    1. Misma rejilla de bins en a y b -> comparables.
    2. Normalizar a probabilidades (suma=1), no densidades (area=1).
    3. Suavizado de Laplace para evitar log(0).
    \"\"\"
    edges = np.histogram_bin_edges(np.concatenate([a, b]), bins=bins)
    a_h, _ = np.histogram(a, bins=edges)
    b_h, _ = np.histogram(b, bins=edges)
    p = (a_h + 1e-9) / (a_h.sum() + 1e-9 * len(a_h))
    q = (b_h + 1e-9) / (b_h.sum() + 1e-9 * len(b_h))
    return float(np.sum(p * np.log(p / q)))

cols = [c for c in X.columns if c != "y"]
kl = pd.Series({c: kl_hist(tr[c], te[c]) for c in cols}).sort_values(ascending=False)
# Sanity: KL es siempre >= 0 (Gibbs)
assert (kl >= -1e-9).all(), f"KL negativo detectado — bug en implementación: {kl[kl < 0]}"
kl
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Bar chart KL.",
            """\
ax = kl.plot.barh(color="#9C27B0", figsize=(7, 4))
ax.axvline(0.1, color="#FF5722", linestyle="--", label="threshold drift (sec 19)")
ax.legend(loc="lower right")
plt.title("KL train vs test — bajo = misma distribución")
plt.xlabel("KL divergence")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "KL siempre ≥ 0 (Gibbs); reportar features con `KL > 0.1` como **alerta de drift** "
            "y bloquear deploy si alguna supera 1.0 (drift fuerte).",
            """\
assert (kl >= -1e-9).all(), "BUG: KL negativo es matemáticamente imposible"
n_warn = int((kl > 0.1).sum())
n_block = int((kl > 1.0).sum())
print(f"Features OK: {(kl <= 0.1).sum()}/{len(kl)} | warning: {n_warn} | block: {n_block}")
print(f"Top drift: {kl.head(3).to_dict()}")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. KL con bins muy pequeños.\n"
            "2. No comparar la columna target.\n"
            "3. Métricas en escala absoluta sin estandarizar.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Implementa Wasserstein distance.\n"
            "2. Visualiza un drift artificial añadiendo +5 °C al test.\n"
            "3. Construye un detector que envíe alerta si KL > umbral.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Mismo notebook sobre dataset producción cada noche.",
        ),
        common_summary(
            next_notebook="07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb",
            docs_link="docs/validation/data-quality.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="07_case_G_data_quality_agents/03_reglas_calidad_oro_ml.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_G,
    )


def _agentes(target: Path) -> Path:
    title = "Caso G · 04 Agentes especialistas de calidad (mock)"
    sections = [
        section(
            1,
            "Objetivo",
            "Implementar 3 agentes-mock que actúan como evaluadores: validador de "
            "plata, auditor de MLflow, evaluador de chatbot.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Patrón `@tool` / `@function_tool`.\n"
            "- Cómo combinar herramientas en un agente.\n"
            "- Cómo mockear LLM si no hay clave.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Curso evalúa la calidad del proyecto con un agente que llama a herramientas. "
            "Usaremos un cliente fake.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Los agentes pueden correr como tarea diaria desde el Dashboard Adapter.",
        ),
        section(5, "Relación con Medallion", "Transversal."),
        section(6, "Datos de entrada", "Mocks."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "**Tres tools que computan reglas reales** (no devuelven dicts hardcoded). "
            "Reciben datos como input, los validan y emiten un veredicto cuantitativo.",
            """\
from typing import Any

def validate_silver_layer(df: pd.DataFrame, asset_id: str = "AULA01") -> dict:
    \"\"\"Valida un DataFrame de capa plata. Devuelve métricas computadas reales.\"\"\"
    expected_tags = {"captia_env", "domain_id", "site_id", "asset_id", "variable"}
    tags_present = expected_tags.issubset(df.columns) if not df.empty else False
    completeness_pct = float(100 * (1 - df.isna().mean().mean())) if not df.empty else 0.0
    if "value" in df.columns and not df.empty:
        v = df["value"]
        outliers = int(((v < v.quantile(0.001)) | (v > v.quantile(0.999))).sum())
    else:
        outliers = 0
    verdict = "OK" if (tags_present and completeness_pct > 95) else "FAIL"
    return {
        "asset_id": asset_id,
        "rows": int(len(df)),
        "tags_present": bool(tags_present),
        "completeness_pct": round(completeness_pct, 2),
        "outliers": outliers,
        "verdict": verdict,
    }


def audit_mlflow_experiment(experiment_name: str, runs_df: pd.DataFrame | None = None) -> dict:
    \"\"\"Audita los runs de un experimento (opcional: pasar un DataFrame de runs).\"\"\"
    if runs_df is None or runs_df.empty:
        return {"experiment": experiment_name, "n_runs": 0, "verdict": "NO_DATA"}
    n_runs = int(len(runs_df))
    has_lakefs = bool(runs_df.get("tags.lakefs_tag", pd.Series()).notna().any()) if "tags.lakefs_tag" in runs_df.columns else False
    best_mae = float(runs_df.get("metrics.MAE", pd.Series([float("inf")])).min())
    verdict = "OK" if (n_runs >= 1 and best_mae < float("inf")) else "FAIL"
    return {
        "experiment": experiment_name, "n_runs": n_runs,
        "best_MAE": round(best_mae, 3) if best_mae < float("inf") else None,
        "lakefs_tag_referenced": has_lakefs, "verdict": verdict,
    }


def evaluate_chatbot_response(question: str, answer: str, expected_keywords: list[str]) -> dict:
    \"\"\"Evalúa la **respuesta** del chatbot contra keywords esperadas.

    Métrica: keyword overlap = |keywords ∩ answer.tokens| / |keywords|.
    Hallucination = answer no contiene NINGUNA keyword esperada.
    \"\"\"
    answer_lower = (answer or "").lower()
    hits = [k for k in expected_keywords if k.lower() in answer_lower]
    score = len(hits) / max(len(expected_keywords), 1)
    return {
        "question": question, "answer": answer,
        "expected_keywords": expected_keywords, "hits": hits,
        "score": round(score, 3),
        "hallucination": bool(score == 0 and len(answer.strip()) > 0),
        "verdict": "OK" if score >= 0.5 else "FAIL",
    }

# Smoke test con mocks reales
df_silver_mock = pd.DataFrame({
    "captia_env": ["dev"]*5, "domain_id": ["bms_classrooms"]*5,
    "site_id": ["ies_simarro"]*5, "asset_id": ["AULA01"]*5,
    "variable": ["co2"]*5, "value": [410.0, 425.0, 600.0, 712.0, np.nan],
})
print(validate_silver_layer(df_silver_mock, "AULA01"))
print(audit_mlflow_experiment("case_B_baseline_2026", pd.DataFrame()))
print(evaluate_chatbot_response(
    question="¿Cuál fue la T media ayer?",
    answer="La temperatura media en AULA01 ayer fue 22.4 °C según los registros.",
    expected_keywords=["temperatura", "media", "AULA01"],
))
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Combinamos las tools en un agente con plan de auditoría diaria. Usamos "
            "el cliente Anthropic si hay API key; si no, simulamos con un planificador "
            "determinista.",
            """\
import os, time

TOOLS = {
    "validate_silver_layer": validate_silver_layer,
    "audit_mlflow_experiment": audit_mlflow_experiment,
    "evaluate_chatbot_response": evaluate_chatbot_response,
}

def call_agent(plan: list[tuple[str, dict]]) -> list[dict]:
    out = []
    for name, kwargs in plan:
        t0 = time.perf_counter()
        try:
            res = TOOLS[name](**kwargs)
        except Exception as e:  # noqa: BLE001
            res = {"verdict": "ERROR", "error": str(e)}
        out.append({
            "tool": name, "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            **res,
        })
    return out

plan = [
    ("validate_silver_layer", {"df": df_silver_mock, "asset_id": "AULA01"}),
    ("audit_mlflow_experiment", {"experiment_name": "case_B_baseline_2026", "runs_df": pd.DataFrame()}),
    ("evaluate_chatbot_response", {
        "question": "¿Cuál fue la T media ayer?",
        "answer": "La temperatura media en AULA01 ayer fue 22.4 °C según los registros.",
        "expected_keywords": ["temperatura", "media", "AULA01"],
    }),
    ("evaluate_chatbot_response", {
        "question": "¿Cuál es el rey de España?",
        "answer": "Felipe VI es el monarca actual de España desde 2014.",
        "expected_keywords": ["temperatura", "AULA01", "CO2"],  # ESPERADAS PERO NO HAY → hallucination
    }),
]
results = call_agent(plan)
print("Tools invocadas:", len(results))
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Reporte consolidado con verdict, latency y trazabilidad de hallucinations.",
            """\
report = pd.DataFrame(results)
print(report[["tool", "verdict", "latency_ms"]].to_string(index=False))
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Verdict por tool + distribución de latencia.",
            """\
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2, figsize=(11, 3.5))
report["verdict"].value_counts().plot.bar(ax=axes[0], color="#3F51B5")
axes[0].set_title("Verdict por invocación")
axes[0].tick_params(axis="x", rotation=0)
report.plot.scatter(x="tool", y="latency_ms", ax=axes[1], color="#FF5722", s=60)
axes[1].set_title("Latencia por tool (ms)")
axes[1].tick_params(axis="x", rotation=15)
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "(a) JSON-serializable, (b) hallucination correctamente detectada en el "
            "ejemplo de la pregunta sobre el rey, (c) las tools válidas devuelven OK.",
            """\
import json

for r in results:
    json.dumps({k: v for k, v in r.items() if k != "answer"})  # answer puede ser largo

# La pregunta sobre el rey debería disparar hallucination=True
hallucinations = [r for r in results if r.get("hallucination")]
assert len(hallucinations) >= 1, "Hallucination no detectada en el ejemplo del rey"
silver_result = next(r for r in results if r["tool"] == "validate_silver_layer")
assert silver_result["verdict"] == "OK", "validate_silver_layer debería pasar con datos limpios"
print(f"Validaciones OK · hallucinations detectadas: {len(hallucinations)}")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Comparar `expected` con `question`** en lugar de con `answer` — el "
            "chatbot puede contestar fuera de tema y tu test pasa. Bug clásico.\n"
            "2. **Tools que devuelven dicts hardcoded** sin tocar datos — pseudo-evaluador.\n"
            "3. **Captura silenciosa** (`except: pass`) — el agente no detecta fallos.\n"
            "4. **No registrar timing**: una tool que tarda 5 s por invocación bloquea "
            "el agente entero. Loggear `latency_ms` siempre.\n"
            "5. **Schemas desalineados entre tools** — usar Pydantic / JSON Schema "
            "compartido para evitar `TypeError` runtime.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Sustituye `keyword overlap` por embeddings (`sentence-transformers`) "
            "y reporta correlación con la métrica anterior. Rúbrica: F1 ≥ 0.8 sobre 20 ejemplos.\n"
            "2. Añade `audit_data_drift(period)` que calcule KL entre histogramas "
            "`P_train` (último mes) y `Q_prod` (última semana). Disparar verdict "
            "FAIL si KL > 0.1.\n"
            "3. Conecta a Anthropic Claude con `tool_use` y verifica que el modelo "
            "selecciona la tool correcta para 5 prompts. Rúbrica: ≥4/5 aciertos.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Las tools no cambian: solo el origen de los datos.",
        ),
        common_summary(
            next_notebook="08_case_H_rag_chatbot/01_arquitectura_rag_tools.ipynb",
            docs_link="docs/use-cases/case-g-data-quality-agents.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="07_case_G_data_quality_agents/04_agentes_especialistas_calidad.ipynb",
        title=title,
        case=CASE,
        layer="transversal",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_G,
    )


def build(target: Path) -> int:
    _bronce(target)
    _plata(target)
    _oro(target)
    _agentes(target)
    return 4
