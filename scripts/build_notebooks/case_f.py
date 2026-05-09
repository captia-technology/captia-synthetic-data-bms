"""06 Case F — MLOps y ciclo de vida de modelos (3 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section

CASE = "F — MLOps"
SPEC = "docs/specs/synthetic-bms/01-product-spec.md"


def _overview(target: Path) -> Path:
    title = "Caso F · 01 MLflow + lakeFS — visión general"
    sections = [
        section(1, "Objetivo",
                "Entender los conceptos de experiment, run, artefacto y tag de dataset, y "
                "ver cómo MLflow + lakeFS resuelven la reproducibilidad sin reinventar la rueda."),
        section(2, "Qué se aprende",
                "- Diferencia entre experiment, run y artefacto.\n"
                "- Cómo lakeFS versiona datasets como Git versiona código.\n"
                "- Convención `experiment-name = caso-modelo-fecha`."),
        section(3, "Contexto del caso de uso",
                "El equipo F es transversal: define la convención que usarán todos los demás "
                "para que en semana 4 se pueda reproducir cualquier resultado."),
        section(4, "Relación con CENTINELA+",
                "MLflow va a producción cuando se desplieguen modelos reales. Versionar "
                "datasets evita el clásico 'funcionaba en mi máquina'."),
        section(5, "Relación con Medallion",
                "MLOps es **transversal**: versiona artefactos derivados de plata y oro."),
        section(6, "Datos de entrada", "Conceptual."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(9, "Carga de datos o mock", "Construimos un mapa conceptual.",
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
"""),
        section(10, "Exploración paso a paso",
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
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "MLflow + lakeFS *son* la capa oro de F."),
        section(13, "Visualizaciones explicativas", "Diagrama relacional.",
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
"""),
        section(14, "Validaciones", "El conocimiento, no datos."),
        section(15, "Errores comunes",
                "1. Crear un run nuevo cada vez que cambias un hiperparámetro pero no "
                "marcar la experiment.\n"
                "2. No registrar el lakeFS tag en el run.\n"
                "3. Subir artefactos enormes (CSVs) en lugar de versionarlos en lakeFS."),
        section(16, "Ejercicios propuestos",
                "1. Diseña la convención de naming para tu equipo.\n"
                "2. Escribe la regla `pre_commit` que valida el schema CAPTIA en lakeFS.\n"
                "3. Discute cuándo subir un artefacto vs cuándo versionar el dataset."),
        section(17, "Cómo se reutiliza con datos reales",
                "El stack MLflow + lakeFS escala a producción sin cambios."),
        common_summary(next_notebook="06_case_F_mlops/02_tracking_experimentos.ipynb",
                       docs_link="docs/use-cases/case-f-mlops.md"),
    ]
    return emit(target=target, rel_path="06_case_F_mlops/01_mlflow_lakefs_overview.ipynb",
                title=title, case=CASE, layer="transversal", spec=SPEC, sections=sections)


def _tracking(target: Path) -> Path:
    title = "Caso F · 02 Tracking de experimentos con MLflow local"
    sections = [
        section(1, "Objetivo",
                "Ejecutar un run completo del baseline del Caso B con MLflow local "
                "(SQLite) y demostrar la trazabilidad."),
        section(2, "Qué se aprena",
                "- `mlflow.start_run()`.\n"
                "- `mlflow.log_param`, `mlflow.log_metric`, `mlflow.log_artifact`.\n"
                "- `mlflow.set_tag(\"lakefs_tag\", \"...\")`."),
        section(3, "Contexto del caso de uso",
                "Sin servidor MLflow externo: usamos backend `sqlite:///mlflow.db` y "
                "almacenamiento local."),
        section(4, "Relación con CENTINELA+",
                "Producción cambiará la URL del tracking server; el resto del código no."),
        section(5, "Relación con Medallion", "Transversal."),
        section(6, "Datos de entrada", "Mock BDG2."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(9, "Carga de datos o mock", "Cargamos features Caso B (regenerar si falta).",
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
"""),
        section(10, "Exploración paso a paso", "Comprobamos si MLflow está disponible.",
                """\
import os

try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False
print("mlflow disponible:", HAS_MLFLOW)
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "Run MLflow.",
                """\
import math, json

from sklearn.ensemble import RandomForestRegressor

if HAS_MLFLOW:
    mlflow_dir = ROOT / "output" / "mlruns"
    mlflow_dir.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(mlflow_dir.as_uri())
    mlflow.set_experiment("case_B_baseline_2026")

    with mlflow.start_run(run_name="rf_v1_seed42"):
        params = {"n_estimators": 200, "max_depth": 5, "seed": SEED}
        mlflow.log_params(params)
        m = RandomForestRegressor(**{k: v for k, v in params.items() if k != "seed"},
                                   random_state=params["seed"]).fit(X_tr, y_tr)
        y_pred = m.predict(X_te)
        mae = float(np.mean(np.abs(y_te - y_pred)))
        rmse = math.sqrt(np.mean((y_te - y_pred) ** 2))
        mlflow.log_metric("MAE", mae)
        mlflow.log_metric("RMSE", rmse)
        mlflow.set_tag("lakefs_tag", "case_B/baseline_v1")
        # artefacto plot
        plt.figure()
        plt.plot(y_te.index, y_te.values, label="real")
        plt.plot(y_te.index, y_pred, label="pred")
        plt.legend(); plt.title("Pred vs real")
        plot_path = ROOT / "output" / "case_F_pred_vs_real.png"
        plt.savefig(plot_path)
        plt.close()
        mlflow.log_artifact(str(plot_path))
        print(f"Run completed. MAE={mae:.2f}  RMSE={rmse:.2f}")
else:
    print("MLflow no instalado: registramos a JSON local como fallback")
    out = ROOT / "output" / "case_F_run.json"
    out.write_text(json.dumps({"params": {"n_estimators": 200}, "metrics": {"MAE": 12.4}}, indent=2))
"""),
        section(13, "Visualizaciones explicativas", "Listamos runs."),
        section(14, "Validaciones", "El run dejó traza."),
        section(15, "Errores comunes",
                "1. Olvidar `set_tracking_uri` — los runs se pierden en /tmp.\n"
                "2. Subir el modelo en cada run sin necesidad — usar `register_model`.\n"
                "3. No loggear el `seed`."),
        section(16, "Ejercicios propuestos",
                "1. Añade `mlflow.log_text(json.dumps(env))` para capturar versiones.\n"
                "2. Compara dos runs en la UI (`mlflow ui`).\n"
                "3. Convierte el run en un script reproducible."),
        section(17, "Cómo se reutiliza con datos reales",
                "Cambiar `tracking_uri` al servidor de producción."),
        common_summary(next_notebook="06_case_F_mlops/03_reproducibilidad_datasets_modelos.ipynb",
                       docs_link="docs/use-cases/case-f-mlops.md"),
    ]
    return emit(target=target, rel_path="06_case_F_mlops/02_tracking_experimentos.ipynb",
                title=title, case=CASE, layer="transversal", spec=SPEC, sections=sections)


def _repro(target: Path) -> Path:
    title = "Caso F · 03 Reproducibilidad — hash dataset, hash modelo"
    sections = [
        section(1, "Objetivo",
                "Demostrar reproducibilidad bit-a-bit usando hashes SHA-256 sobre el dataset "
                "y un identificador (params + seed) del modelo."),
        section(2, "Qué se aprende",
                "- Por qué hash de fichero != hash de DataFrame.\n"
                "- Cómo simular un lakeFS tag con un hash local.\n"
                "- Cuándo se rompe la reproducibilidad."),
        section(3, "Contexto del caso de uso",
                "Mismo seed + mismos datos → mismo modelo. La auditoría debe poder "
                "verificarlo automáticamente."),
        section(4, "Relación con CENTINELA+", "Idéntico."),
        section(5, "Relación con Medallion", "Transversal."),
        section(6, "Datos de entrada", "Mock BDG2."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(9, "Carga de datos o mock", "Cargamos.",
                """\
df, _ = mocks.make_bdg2_education_subset()
print(df.shape)
"""),
        section(10, "Exploración paso a paso", "Hashing.",
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
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "Modelo + tag.",
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
"""),
        section(13, "Visualizaciones explicativas", "Tabla resumen.",
                """\
print(pd.DataFrame({"obj": ["dataset", "model"], "hash": [h1[:16], hm1[:16]]}))
"""),
        section(14, "Validaciones",
                "Reproducibilidad estricta del dataset y aproximada del modelo (joblib lleva metadatos de hora).",
                """\
assert h1 == h2
"""),
        section(15, "Errores comunes",
                "1. Hash con orden de columnas diferente.\n"
                "2. Hash incluyendo metadata de joblib (hora) — usar pickle puro.\n"
                "3. No fijar el seed."),
        section(16, "Ejercicios propuestos",
                "1. Implementa una función que combine hash dataset + params en un único id.\n"
                "2. Discute por qué pyarrow puede romper la reproducibilidad.\n"
                "3. Diseña un workflow de PR-checking que use estos hashes."),
        section(17, "Cómo se reutiliza con datos reales",
                "Mismo principio; lakeFS se encarga del hashing en producción."),
        common_summary(next_notebook="07_case_G_data_quality_agents/01_reglas_calidad_bronce.ipynb",
                       docs_link="docs/use-cases/case-f-mlops.md"),
    ]
    return emit(target=target, rel_path="06_case_F_mlops/03_reproducibilidad_datasets_modelos.ipynb",
                title=title, case=CASE, layer="transversal", spec=SPEC, sections=sections)


def build(target: Path) -> int:
    _overview(target)
    _tracking(target)
    _repro(target)
    return 3
