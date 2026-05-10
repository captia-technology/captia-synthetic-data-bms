"""06 Case F — MLOps y ciclo de vida de modelos (3 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_CASE_F

CASE = "F — MLOps"
SPEC = "docs/specs/synthetic-bms/01-product-spec.md"


def _overview(target: Path) -> Path:
    title = "Caso F · 01 MLflow + lakeFS — visión general"
    sections = [
        section(
            1,
            "Objetivo",
            "Entender los conceptos de experiment, run, artefacto y tag de dataset, y "
            "ver cómo MLflow + lakeFS resuelven la reproducibilidad sin reinventar la rueda.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Diferencia entre experiment, run y artefacto.\n"
            "- Cómo lakeFS versiona datasets como Git versiona código.\n"
            "- Convención `experiment-name = caso-modelo-fecha`.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El equipo F es transversal: define la convención que usarán todos los demás "
            "para que en semana 4 se pueda reproducir cualquier resultado.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "MLflow va a producción cuando se desplieguen modelos reales. Versionar "
            "datasets evita el clásico 'funcionaba en mi máquina'.",
        ),
        section(
            5,
            "Relación con Medallion",
            "MLOps es **transversal**: versiona artefactos derivados de plata y oro.",
        ),
        section(6, "Datos de entrada", "Conceptual."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Construimos un mapa conceptual.",
            """\
mlflow_concepts = pd.DataFrame(
    [
        ("Experiment", "Agrupación lógica", "case_B_baseline_2026"),
        ("Run", "Ejecución concreta", "rf_v3_seed42"),
        ("Param", "Hiperparámetro", "n_estimators=200"),
        ("Metric", "Indicador", "MAE=12.4"),
        ("Artifact", "Modelo / plot / dataset", "model.pkl, residuos.png"),
        ("Tag", "Metadata libre", "stage=staging"),
    ],
    columns=["objeto", "papel", "ejemplo"],
)
mlflow_concepts
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "lakeFS funciona como Git pero para datos: branches, commits y tags.",
            """\
lakefs_concepts = pd.DataFrame(
    [
        ("Repository", "Bucket lógico (S3 backend)", "captia-datasets"),
        ("Branch", "Línea de trabajo", "main / experiment-Y"),
        ("Commit", "Snapshot inmutable", "deadbeef"),
        ("Tag", "Etiqueta humana", "case_B/baseline_v1"),
        ("Hooks", "Validaciones pre/post commit", "schema check"),
    ],
    columns=["objeto", "papel", "ejemplo"],
)
lakefs_concepts
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "MLflow + lakeFS *son* la capa oro de F."),
        section(
            13,
            "Visualizaciones explicativas",
            "Diagrama relacional.",
            """\
from IPython.display import Markdown
Markdown('''```mermaid
flowchart LR
  D[(lakeFS\\nDataset versionado)] --> R[MLflow Run]
  R --> A[Artefactos\\nmodel.pkl + plots]
  R --> M[Métricas\\nMAE/MAPE/RMSE]
  R --> T[Tag\\nlakeFS_tag=...]
  T --> D
```''')
""",
        ),
        section(14, "Validaciones", "El conocimiento, no datos."),
        section(
            15,
            "Errores comunes",
            "1. Crear un run nuevo cada vez que cambias un hiperparámetro pero no "
            "marcar la experiment.\n"
            "2. No registrar el lakeFS tag en el run.\n"
            "3. Subir artefactos enormes (CSVs) en lugar de versionarlos en lakeFS.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Diseña la convención de naming para tu equipo.\n"
            "2. Escribe la regla `pre_commit` que valida el schema CAPTIA en lakeFS.\n"
            "3. Discute cuándo subir un artefacto vs cuándo versionar el dataset.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "El stack MLflow + lakeFS escala a producción sin cambios.",
        ),
        common_summary(
            next_notebook="06_case_F_mlops/02_tracking_experimentos.ipynb",
            docs_link="docs/use-cases/case-f-mlops.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="06_case_F_mlops/01_mlflow_lakefs_overview.ipynb",
        title=title,
        case=CASE,
        layer="transversal",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_F,
    )


def _tracking(target: Path) -> Path:
    title = "Caso F · 02 Tracking de experimentos con MLflow local"
    sections = [
        section(
            1,
            "Objetivo",
            "Ejecutar un run completo del baseline del Caso B con MLflow local "
            "(SQLite) y demostrar la trazabilidad.",
        ),
        section(
            2,
            "Qué se aprena",
            "- `mlflow.start_run()`.\n"
            "- `mlflow.log_param`, `mlflow.log_metric`, `mlflow.log_artifact`.\n"
            '- `mlflow.set_tag("lakefs_tag", "...")`.',
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Sin servidor MLflow externo: usamos backend `sqlite:///mlflow.db` y "
            "almacenamiento local.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Producción cambiará la URL del tracking server; el resto del código no.",
        ),
        section(5, "Relación con Medallion", "Transversal."),
        section(6, "Datos de entrada", "Mock BDG2."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos features Caso B (regenerar si falta).",
            """\
df, _ = mocks.make_bdg2_education_subset()
df = df[df.building_id == df.building_id.unique()[0]].set_index("timestamp")
X = pd.DataFrame({
    "y": df["power_kw"],
    "t_outdoor": df["t_outdoor"],
    "lag_24h": df["power_kw"].shift(24),
}).dropna()
y = X.pop("y")
n = len(X); i = int(n * 0.8)
X_tr, X_te = X.iloc[:i], X.iloc[i:]
y_tr, y_te = y.iloc[:i], y.iloc[i:]
print(len(X_tr), len(X_te))
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Comprobamos si MLflow está disponible.",
            """\
import os

try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False
print("mlflow disponible:", HAS_MLFLOW)
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "**Tres runs comparables** para que el alumno vea MLflow funcionando: "
            "(1) baseline naïve-24h sin entrenamiento, (2) RF con 100 árboles, "
            "(3) RF con 300 árboles + max_depth 8. Loggea params + métricas + el "
            "improvement vs naïve para cada uno.",
            """\
import math
from sklearn.ensemble import RandomForestRegressor
from notebooks._common.eval_helpers import naive_persistence_24h, mae as _mae, rmse as _rmse

assert HAS_MLFLOW, "MLflow es obligatorio para este notebook (`uv sync --group notebooks`)"

mlflow_dir = ROOT / "output" / "mlruns"
mlflow_dir.mkdir(parents=True, exist_ok=True)
mlflow.set_tracking_uri(mlflow_dir.as_uri())
mlflow.set_experiment("case_B_baseline_2026")

# Baseline naïve-24h (referencia obligatoria)
y_naive = naive_persistence_24h(y_tr, y_te)
mae_naive = _mae(y_te.to_numpy(), y_naive)

runs = [
    {"name": "rf_n100_d5",  "n_estimators": 100, "max_depth": 5},
    {"name": "rf_n300_d8",  "n_estimators": 300, "max_depth": 8},
]

run_ids = []
for cfg in runs:
    with mlflow.start_run(run_name=cfg["name"]) as run:
        mlflow.log_params({**cfg, "seed": SEED})
        m = RandomForestRegressor(
            n_estimators=cfg["n_estimators"], max_depth=cfg["max_depth"],
            random_state=SEED, n_jobs=1,
        ).fit(X_tr, y_tr)
        y_pred = m.predict(X_te)
        mae_m = _mae(y_te.to_numpy(), y_pred)
        rmse_m = _rmse(y_te.to_numpy(), y_pred)
        improvement = (1 - mae_m / mae_naive) * 100 if mae_naive > 0 else 0
        mlflow.log_metric("MAE", mae_m)
        mlflow.log_metric("RMSE", rmse_m)
        mlflow.log_metric("MAE_naive", mae_naive)
        mlflow.log_metric("MAE_improvement_pct", improvement)
        mlflow.set_tag("lakefs_tag", "case_B/baseline_v1")
        mlflow.set_tag("baseline", "naive_persistence_24h")
        # artefact plot
        plt.figure(figsize=(10, 3))
        plt.plot(y_te.index, y_te.values, label="real", color="#3F51B5", linewidth=1)
        plt.plot(y_te.index, y_pred, label="pred", color="#FF5722", linewidth=1, alpha=0.9)
        plt.plot(y_te.index, y_naive, label="naive_24h", color="gray", linewidth=0.7, alpha=0.7)
        plt.legend(loc="upper right", fontsize=8)
        plt.title(f"{cfg['name']}: MAE={mae_m:.2f} (vs naive={mae_naive:.2f}, +{improvement:.1f}%)")
        plot_path = ROOT / "output" / f"case_F_{cfg['name']}.png"
        plt.savefig(plot_path, dpi=120, bbox_inches="tight")
        plt.close()
        mlflow.log_artifact(str(plot_path))
        run_ids.append(run.info.run_id)
        print(f"  {cfg['name']}: MAE={mae_m:.2f}  RMSE={rmse_m:.2f}  vs naive +{improvement:.1f}%")
print(f"\\n{len(run_ids)} runs registrados en {mlflow_dir.as_uri()}")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Listamos los runs en la experiment con `mlflow.search_runs()` y "
            "comparamos métricas en una tabla.",
            """\
runs_df = mlflow.search_runs(experiment_names=["case_B_baseline_2026"], output_format="pandas")
cols = ["tags.mlflow.runName", "metrics.MAE", "metrics.RMSE",
        "metrics.MAE_improvement_pct", "params.n_estimators", "params.max_depth"]
present = [c for c in cols if c in runs_df.columns]
runs_summary = runs_df[present].sort_values("metrics.MAE")
print(runs_summary.to_string(index=False))
""",
        ),
        section(
            14,
            "Validaciones",
            "Cada run debe (a) batir la línea naïve-24h en MAE y (b) tener "
            "`MAE_improvement_pct > 0`.",
            """\
for run_id in run_ids:
    run = mlflow.get_run(run_id)
    mae_m = run.data.metrics["MAE"]
    impr = run.data.metrics["MAE_improvement_pct"]
    assert mae_m < mae_naive, f"Run {run.info.run_name} no bate naive ({mae_m:.2f} >= {mae_naive:.2f})"
    assert impr > 0, f"Improvement no positivo en {run.info.run_name}"
print("Validaciones OK — todos los runs baten naive-24h")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Olvidar `set_tracking_uri` — los runs se pierden en /tmp.\n"
            "2. Subir el modelo en cada run sin necesidad — usar `register_model`.\n"
            "3. No loggear el `seed`.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `mlflow.log_text(json.dumps(env))` para capturar versiones.\n"
            "2. Compara dos runs en la UI (`mlflow ui`).\n"
            "3. Convierte el run en un script reproducible.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cambiar `tracking_uri` al servidor de producción.",
        ),
        common_summary(
            next_notebook="06_case_F_mlops/03_reproducibilidad_datasets_modelos.ipynb",
            docs_link="docs/use-cases/case-f-mlops.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="06_case_F_mlops/02_tracking_experimentos.ipynb",
        title=title,
        case=CASE,
        layer="transversal",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_F,
    )


def _repro(target: Path) -> Path:
    title = "Caso F · 03 Reproducibilidad — hash dataset, hash modelo"
    sections = [
        section(
            1,
            "Objetivo",
            "Demostrar reproducibilidad bit-a-bit usando hashes SHA-256 sobre el dataset "
            "y un identificador (params + seed) del modelo.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Por qué hash de fichero != hash de DataFrame.\n"
            "- Cómo simular un lakeFS tag con un hash local.\n"
            "- Cuándo se rompe la reproducibilidad.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Mismo seed + mismos datos → mismo modelo. La auditoría debe poder "
            "verificarlo automáticamente.",
        ),
        section(4, "Relación con CENTINELA+", "Idéntico."),
        section(5, "Relación con Medallion", "Transversal."),
        section(6, "Datos de entrada", "Mock BDG2."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos.",
            """\
df, _ = mocks.make_bdg2_education_subset()
print(df.shape)
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Hashing.",
            """\
import hashlib

def df_hash(df: pd.DataFrame) -> str:
    rep = df.sort_index(axis=1).to_csv(index=False).encode()
    return hashlib.sha256(rep).hexdigest()

h1 = df_hash(df)
df_again, _ = mocks.make_bdg2_education_subset()
h2 = df_hash(df_again)
print("hash 1:", h1[:16])
print("hash 2:", h2[:16])
assert h1 == h2, "Reproducibilidad rota"
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Modelo + tag.",
            """\
from sklearn.ensemble import RandomForestRegressor

X = pd.DataFrame({
    "y": df["power_kw"], "t": df["t_outdoor"], "ghi": df["ghi"],
}).dropna()
y = X.pop("y")
m1 = RandomForestRegressor(n_estimators=50, random_state=SEED).fit(X, y)
m2 = RandomForestRegressor(n_estimators=50, random_state=SEED).fit(X, y)
import joblib, io
b1 = io.BytesIO(); joblib.dump(m1, b1)
b2 = io.BytesIO(); joblib.dump(m2, b2)
hm1 = hashlib.sha256(b1.getvalue()).hexdigest()
hm2 = hashlib.sha256(b2.getvalue()).hexdigest()
print(hm1[:16], hm2[:16])
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Tabla resumen.",
            """\
print(pd.DataFrame({"obj": ["dataset", "model"], "hash": [h1[:16], hm1[:16]]}))
""",
        ),
        section(
            14,
            "Validaciones",
            "Reproducibilidad estricta del dataset y aproximada del modelo (joblib lleva metadatos de hora).",
            """\
assert h1 == h2
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Hash con orden de columnas diferente.\n"
            "2. Hash incluyendo metadata de joblib (hora) — usar pickle puro.\n"
            "3. No fijar el seed.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Implementa una función que combine hash dataset + params en un único id.\n"
            "2. Discute por qué pyarrow puede romper la reproducibilidad.\n"
            "3. Diseña un workflow de PR-checking que use estos hashes.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Mismo principio; lakeFS se encarga del hashing en producción.",
        ),
        common_summary(
            next_notebook="07_case_G_data_quality_agents/01_reglas_calidad_bronce.ipynb",
            docs_link="docs/use-cases/case-f-mlops.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="06_case_F_mlops/03_reproducibilidad_datasets_modelos.ipynb",
        title=title,
        case=CASE,
        layer="transversal",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_F,
    )


def build(target: Path) -> int:
    _overview(target)
    _tracking(target)
    _repro(target)
    return 3
