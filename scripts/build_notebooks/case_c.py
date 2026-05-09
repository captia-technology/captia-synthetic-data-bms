"""03 Case C — Detección de anomalías HVAC (5 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section

CASE = "C — Anomalías HVAC"
SPEC = "docs/specs/synthetic-bms/02-domain-spec.md"


def _eda(target: Path) -> Path:
    title = "Caso C · 01 EDA HVAC y catálogo de fallos"
    sections = [
        section(1, "Objetivo",
                "Conocer el dataset LBNL FDD (mock RTU) con 4 tipos de fallos etiquetados, "
                "identificar la firma de cada fallo en sensores y construir el catálogo del "
                "Caso C."),
        section(2, "Qué se aprende",
                "- 4 tipos de fallos HVAC y cómo se manifiestan.\n"
                "- Variables: T_supply, T_return, valve, fan, occupancy.\n"
                "- Conceptos ΔT, duty cycle, ratio fan/valve.\n"
                "- Cómo separar fallos en clases supervisadas."),
        section(3, "Contexto del caso de uso",
                "Datos sintéticos del generador `caseC_faults.yaml` o LBNL FDD reducido. "
                "Las etiquetas viven en `captia_fault_labels` (measurement separado)."),
        section(4, "Relación con CENTINELA+",
                "El sistema real puede sufrir estos 4 tipos. La descripción cualitativa "
                "fue solicitada a CAPTIA en el informe de mayo."),
        section(5, "Relación con Medallion",
                "Bronce mock LBNL FDD; etiquetas las usaremos para el supervised eval."),
        section(6, "Datos de entrada",
                "`notebooks/_data/lbnl_fdd_rtu_mock.csv`."),
        section(7, "Schema CAPTIA esperado",
                "Mapping LBNL → CAPTIA visto en docs:\n\n"
                "| LBNL | CAPTIA | bucket |\n|---|---|---|\n"
                "| `SA_TEMP` | `temperature_supply` | telemetry |\n"
                "| `RA_TEMP` | `temperature_return` | telemetry |\n"
                "| `OA_TEMP` | `temperature_outdoor` | telemetry |\n"
                "| `CCV` | `valve_control` | state_events |\n"
                "| `FAN_STATE` | `fan_speed_01_state` | state_events |\n"
                "| `OCCU_MOD` | `occupancy` | telemetry |\n"
                "Etiquetas → `captia_fault_labels` (state_events)."),
        setup_section(),
        section(9, "Carga de datos o mock",
                "Cargamos el mock con cabecera explícita.",
                """\
csv_path = ROOT / "notebooks" / "_data" / "lbnl_fdd_rtu_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"]).sort_values("timestamp")
df.head()
"""),
        section(10, "Exploración paso a paso",
                "Distribución de los tipos de fallo.",
                """\
print(df["fault_type"].value_counts())
"""),
        section(11, "Transformación bronce → plata",
                "(Lo veremos en el siguiente notebook.) Aquí calculamos features para EDA.",
                """\
df["dt_supply_return"] = df["RA_TEMP"] - df["SA_TEMP"]
df["dt_supply_outdoor"] = df["OA_TEMP"] - df["SA_TEMP"]
df["fan_eff"] = df["CCV"] - df["FAN_STATE"]  # idealmente 0; >0 = válvula abierta sin fan
df.head()
"""),
        section(12, "Construcción de capa oro",
                "(Notebook 03)."),
        section(13, "Visualizaciones explicativas",
                "T_supply durante valve_stuck (debería NO bajar pese a CCV=1).",
                """\
mask = df["fault_type"] == "valve_stuck"
if mask.any():
    win = df.loc[mask].head(120)
    plt.figure(figsize=(10, 3))
    plt.plot(win["timestamp"], win["SA_TEMP"], label="SA", color="#3F51B5")
    plt.plot(win["timestamp"], win["RA_TEMP"], label="RA", color="#FF5722")
    plt.plot(win["timestamp"], win["CCV"] * 5 + 18, label="valve x5", color="#4CAF50")
    plt.legend()
    plt.title("Valve stuck — T_supply no baja")
    plt.tight_layout()
"""),
        section(14, "Validaciones",
                "Las etiquetas deben sumar al menos 5% del dataset (mocked).",
                """\
ratio = (df["is_fault"] == 1).mean()
print("Fault ratio:", ratio)
assert 0.05 <= ratio <= 0.6
"""),
        section(15, "Errores comunes",
                "1. Asumir que el dataset solo tiene fallo→entonces el modelo no aprende lo normal.\n"
                "2. Concatenar fallos sin solapamiento (el mock incluye solapamientos).\n"
                "3. Mezclar `is_fault` y `fault_type` en el mismo modelo sin preprocesar."),
        section(16, "Ejercicios propuestos",
                "1. Cuenta cuántos episodios de cada tipo (no puntos).\n"
                "2. Visualiza ΔT durante refrigerant_low.\n"
                "3. Estima la duración media por tipo de fallo."),
        section(17, "Cómo se reutiliza con datos reales",
                "LBNL FDD real tiene mismo schema. Para CENTINELA+ los fallos vienen de "
                "tickets manuales — convertir a `captia_fault_labels`."),
        common_summary(next_notebook="03_case_C_hvac_anomaly_detection/02_bronze_to_silver_hvac.ipynb",
                       docs_link="docs/use-cases/case-c-hvac-anomaly.md"),
    ]
    return emit(target=target, rel_path="03_case_C_hvac_anomaly_detection/01_eda_hvac_fdd.ipynb",
                title=title, case=CASE, layer="bronce", spec=SPEC, sections=sections)


def _bronze_silver(target: Path) -> Path:
    title = "Caso C · 02 ETL bronce → plata HVAC + etiquetas en captia_fault_labels"
    sections = [
        section(1, "Objetivo",
                "Mapear LBNL FDD a CAPTIA, generar line protocol para `temperature_supply`, "
                "`temperature_return`, `valve_control`, `fan_speed_01_state` y, por separado, "
                "los eventos de fallo en `captia_fault_labels`."),
        section(2, "Qué se aprende",
                "- Routing on-change vs continuo.\n"
                "- Por qué las etiquetas no van con la telemetría.\n"
                "- Cómo emitir un evento `active=1` al inicio y `active=0` al fin."),
        section(3, "Contexto del caso de uso",
                "El equipo C necesita preservar la trazabilidad: dado un timestamp puede "
                "responder ¿hay fallo activo aquí? sin contaminar `captia_point`."),
        section(4, "Relación con CENTINELA+",
                "Mismo enfoque que producción real: telemetría limpia + labels separados."),
        section(5, "Relación con Medallion",
                "Bronce → plata + etiquetas en bucket `state_events` separado."),
        section(6, "Datos de entrada",
                "`lbnl_fdd_rtu_mock.csv`."),
        section(7, "Schema CAPTIA esperado",
                "Para etiquetas:\n"
                "```\n"
                "captia_fault_labels,captia_env=dev,domain_id=hvac_system,site_id=lbnl_building59,asset_id=RTU_01,fault_type=valve_stuck active=1.0i,severity=0.74 <ts>\n"
                "captia_fault_labels,...,fault_type=valve_stuck active=0.0i <ts>\n"
                "```"),
        setup_section(),
        section(9, "Carga de datos o mock",
                "Cargamos y agrupamos episodios.",
                """\
csv_path = ROOT / "notebooks" / "_data" / "lbnl_fdd_rtu_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
df.head()
"""),
        section(10, "Exploración paso a paso",
                "Detectamos los episodios de fallo (transiciones).",
                """\
df["episode_start"] = (df["fault_type"] != df["fault_type"].shift(fill_value="normal"))
episodes = df.loc[df["episode_start"]].copy()
print("Total transiciones:", len(episodes))
episodes.head()
"""),
        section(11, "Transformación bronce → plata",
                "Generamos line protocol para telemetría continua y para etiquetas.",
                """\
out_dir = ROOT / "output" / "case_C"
out_dir.mkdir(parents=True, exist_ok=True)

VARMAP = {
    "SA_TEMP": "temperature_supply",
    "RA_TEMP": "temperature_return",
    "OA_TEMP": "temperature_outdoor",
}
def to_lp_telemetry(row, csv_col, captia_var):
    ts_ns = int(pd.Timestamp(row["timestamp"]).value)
    return build_line_protocol(
        measurement=MEASUREMENT_TELEMETRY,
        tags={"captia_env": "dev", "domain_id": "hvac_system",
              "site_id": "lbnl_building59", "asset_id": "RTU_01",
              "variable": captia_var},
        fields={"value": float(row[csv_col])},
        timestamp_ns=ts_ns,
    )

# Solo primeras 500 filas para clase
sample = df.head(500)
lines_telem = [to_lp_telemetry(r, c, v) for c, v in VARMAP.items() for _, r in sample.iterrows()]
(out_dir / "hvac_telemetry.lp").write_text("\\n".join(lines_telem) + "\\n", encoding="utf-8")
print(f"Telemetry: {len(lines_telem)} líneas")
"""),
        section(12, "Construcción de capa oro",
                "Para etiquetas: emitimos `active=1` al iniciar episodio y `active=0` al "
                "finalizar.",
                """\
labels_lp = []
fault_runs = (df["fault_type"] != df["fault_type"].shift()).cumsum()
for run, grp in df.groupby(fault_runs):
    ftype = grp["fault_type"].iloc[0]
    if ftype == "normal":
        continue
    start_ts = int(pd.Timestamp(grp["timestamp"].iloc[0]).value)
    end_ts = int(pd.Timestamp(grp["timestamp"].iloc[-1]).value)
    labels_lp.append(
        f"captia_fault_labels,captia_env=dev,domain_id=hvac_system,site_id=lbnl_building59,asset_id=RTU_01,fault_type={ftype} "
        f"active=1i,severity=0.74 {start_ts}"
    )
    labels_lp.append(
        f"captia_fault_labels,captia_env=dev,domain_id=hvac_system,site_id=lbnl_building59,asset_id=RTU_01,fault_type={ftype} "
        f"active=0i {end_ts}"
    )
(out_dir / "hvac_fault_labels.lp").write_text("\\n".join(labels_lp) + "\\n", encoding="utf-8")
print(f"Etiquetas: {len(labels_lp)} eventos (start+end)")
"""),
        section(13, "Visualizaciones explicativas",
                "Bar chart episodios por tipo.",
                """\
runs_summary = (
    df.assign(run=fault_runs)
      .query("fault_type != 'normal'")
      .groupby(["run", "fault_type"]).size()
      .reset_index(name="duration_min")
)
runs_summary["fault_type"].value_counts().plot.bar(color="#9C27B0")
plt.title("Episodios por tipo de fallo")
plt.tight_layout()
"""),
        section(14, "Validaciones",
                "Etiquetas no contaminan la telemetría (measurement diferente).",
                """\
assert "captia_fault_labels" in labels_lp[0]
assert "captia_point" not in labels_lp[0]
print("Schema OK — etiquetas separadas")
"""),
        section(15, "Errores comunes",
                "1. Mezclar `is_fault` como tag de `captia_point` (rompe cardinalidad).\n"
                "2. Olvidar emitir el `active=0` al final (queda fallo abierto eternamente).\n"
                "3. No usar `fault_type` como tag — perdemos granularidad."),
        section(16, "Ejercicios propuestos",
                "1. Añade severity proporcional a la duración del episodio.\n"
                "2. Implementa solapamiento: dos fallos simultáneos.\n"
                "3. Calcula MTBF (Mean Time Between Failures)."),
        section(17, "Cómo se reutiliza con datos reales",
                "Para fallos reales del IES Simarro, la fuente serían tickets de mantenimiento. "
                "Conviértelos a este formato y pásalos por el mismo ETL."),
        common_summary(next_notebook="03_case_C_hvac_anomaly_detection/03_features_anomalias_hvac.ipynb",
                       docs_link="docs/contracts/medallion-layers.md"),
    ]
    return emit(target=target, rel_path="03_case_C_hvac_anomaly_detection/02_bronze_to_silver_hvac.ipynb",
                title=title, case=CASE, layer="bronce → plata", spec=SPEC, sections=sections)


def _features(target: Path) -> Path:
    title = "Caso C · 03 Features para detección de anomalías HVAC"
    sections = [
        section(1, "Objetivo", "Construir features que separen normal de fallo: ΔT, duty cycles, "
                "ratios fan/valve, lags."),
        section(2, "Qué se aprende",
                "- ΔT como indicador de transferencia de calor.\n"
                "- Duty cycle del HVAC (% on en una ventana).\n"
                "- Ratio anomalía cuando válvula activa pero fan apagado.\n"
                "- Por qué los autoencoders prefieren features escaladas."),
        section(3, "Contexto del caso de uso",
                "Las features físicamente significativas mejoran la interpretabilidad y "
                "reducen el espacio de búsqueda."),
        section(4, "Relación con CENTINELA+",
                "Mismas features se calcularían sobre `simarro-prod` cuando llegue un "
                "ticket de incidencia — para reproducir la firma."),
        section(5, "Relación con Medallion",
                "Lee plata, escribe oro local."),
        section(6, "Datos de entrada",
                "Plata mock (CSV) + etiquetas."),
        section(7, "Schema CAPTIA esperado",
                "No aplica para oro (parquet)."),
        setup_section(),
        section(9, "Carga de datos o mock",
                "Cargamos plata y etiquetas.",
                """\
csv_path = ROOT / "notebooks" / "_data" / "lbnl_fdd_rtu_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"]).sort_values("timestamp").set_index("timestamp")
df.head()
"""),
        section(10, "Exploración paso a paso", "Computamos features y discutimos cobertura.",
                """\
def make_features(d):
    f = pd.DataFrame(index=d.index)
    f["dt_supply_return"] = d["RA_TEMP"] - d["SA_TEMP"]
    f["dt_supply_outdoor"] = d["OA_TEMP"] - d["SA_TEMP"]
    f["valve"] = d["CCV"]
    f["fan"] = d["FAN_STATE"]
    f["fan_valve_diff"] = f["valve"] - f["fan"]
    f["valve_duty_60"] = f["valve"].rolling("60min").mean()
    f["fan_duty_60"] = f["fan"].rolling("60min").mean()
    f["dt_lag_15"] = f["dt_supply_return"].shift(15)
    f["dt_change_15"] = f["dt_supply_return"] - f["dt_lag_15"]
    f["is_fault"] = d["is_fault"]
    f["fault_type"] = d["fault_type"]
    return f.dropna()

X = make_features(df)
X.head()
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "Persistimos.",
                """\
out_dir = ROOT / "output" / "case_C"
out_dir.mkdir(parents=True, exist_ok=True)
parquet_path = out_dir / "hvac_features.parquet"
X.drop(columns=["fault_type"]).to_parquet(parquet_path)
print(f"Wrote {parquet_path.relative_to(ROOT)} ({len(X)})")
"""),
        section(13, "Visualizaciones explicativas",
                "Distribución de `dt_supply_return` separada por `is_fault`.",
                """\
plot_distribution(X.assign(grupo=np.where(X.is_fault == 1, "fault", "normal")),
                  column="dt_supply_return", by="grupo", title="ΔT_return-supply normal vs fallo")
"""),
        section(14, "Validaciones", "El target debe estar balanceado lo suficiente.",
                """\
counts = X["is_fault"].value_counts(normalize=True)
print(counts)
assert counts.min() > 0.02
"""),
        section(15, "Errores comunes",
                "1. **Olvidar shift en rolling**: leakage.\n"
                "2. **Usar lag mayor que ventana**: NaN al inicio.\n"
                "3. **Mezclar fallos en mismo modelo binario sin codificar tipo**."),
        section(16, "Ejercicios propuestos",
                "1. Añade `valve_duty_15` y compara feature importance.\n"
                "2. Discute si SHAP funcionaría mejor con o sin escalado.\n"
                "3. Construye `fault_id` único por episodio."),
        section(17, "Cómo se reutiliza con datos reales",
                "`make_features` es pura: misma función sobre cualquier `simarro-prod` data."),
        common_summary(next_notebook="03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder.ipynb",
                       docs_link="docs/use-cases/case-c-hvac-anomaly.md"),
    ]
    return emit(target=target, rel_path="03_case_C_hvac_anomaly_detection/03_features_anomalias_hvac.ipynb",
                title=title, case=CASE, layer="oro", spec=SPEC, sections=sections)


def _models(target: Path) -> Path:
    title = "Caso C · 04 Isolation Forest + Autoencoder"
    sections = [
        section(1, "Objetivo", "Entrenar Isolation Forest (no supervisado) y un Autoencoder "
                "MLP simple. Comparar AUC cuando reservamos las etiquetas para validación."),
        section(2, "Qué se aprende",
                "- Isolation Forest: hiperparámetros y score.\n"
                "- Autoencoder MLP: reconstruction error como score.\n"
                "- Cuándo no supervisado es mejor que supervisado.\n"
                "- Threshold tuning con percentiles."),
        section(3, "Contexto del caso de uso",
                "El equipo C entrega un detector que opera en producción sin etiquetas — "
                "porque en CENTINELA+ los fallos reales son raros."),
        section(4, "Relación con CENTINELA+",
                "El detector se conecta como tool al chatbot Caso H (`check_hvac_anomaly`)."),
        section(5, "Relación con Medallion", "Oro: modelo entrenado."),
        section(6, "Datos de entrada", "Oro features Caso C."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(9, "Carga de datos o mock", "Reusamos las features.",
                """\
parquet_path = ROOT / "output" / "case_C" / "hvac_features.parquet"
if parquet_path.exists():
    X = pd.read_parquet(parquet_path)
else:
    df, _ = mocks.make_lbnl_fdd_rtu_mock()
    X = pd.DataFrame({
        "dt_supply_return": df["RA_TEMP"] - df["SA_TEMP"],
        "valve": df["CCV"],
        "fan": df["FAN_STATE"],
        "is_fault": df["is_fault"],
    }, index=df["timestamp"]).dropna()
print(X.shape)
"""),
        section(10, "Exploración paso a paso", "Split: entrenar Isolation Forest sobre lo "
                "que llamamos 'normal' (puede contener trazas; no rompe).",
                """\
y = X.pop("is_fault").astype(int)
from sklearn.ensemble import IsolationForest
iso = IsolationForest(contamination=0.1, random_state=SEED, n_estimators=200)
iso.fit(X)
score_iso = -iso.score_samples(X)  # mayor = más anómalo
print("score range:", score_iso.min().round(3), score_iso.max().round(3))
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "Autoencoder simple sin dependencias pesadas.",
                """\
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler().fit(X)
Xs = scaler.transform(X)
ae = MLPRegressor(hidden_layer_sizes=(8, 4, 8), max_iter=400, random_state=SEED).fit(Xs, Xs)
recon = ae.predict(Xs)
score_ae = np.mean((Xs - recon) ** 2, axis=1)
print("AE score range:", score_ae.min().round(3), score_ae.max().round(3))
"""),
        section(13, "Visualizaciones explicativas", "ROC de cada modelo.",
                """\
from sklearn.metrics import roc_auc_score, roc_curve
fpr_i, tpr_i, _ = roc_curve(y, score_iso)
fpr_a, tpr_a, _ = roc_curve(y, score_ae)
auc_i = roc_auc_score(y, score_iso)
auc_a = roc_auc_score(y, score_ae)
plt.figure(figsize=(6, 5))
plt.plot(fpr_i, tpr_i, label=f"IF AUC={auc_i:.3f}", color="#3F51B5")
plt.plot(fpr_a, tpr_a, label=f"AE AUC={auc_a:.3f}", color="#FF5722")
plt.plot([0, 1], [0, 1], "--", color="gray")
plt.xlabel("FPR"); plt.ylabel("TPR"); plt.legend(); plt.title("ROC HVAC anomaly")
plt.tight_layout()
print({"AUC_IF": auc_i, "AUC_AE": auc_a})
"""),
        section(14, "Validaciones", "Ambos AUC > 0.7 sobre el mock.",
                """\
assert auc_i > 0.7 and auc_a > 0.7
"""),
        section(15, "Errores comunes",
                "1. **Entrenar sobre todo y evaluar sobre todo**: contaminación.\n"
                "2. **Threshold fijo**: usar percentil sobre el train.\n"
                "3. **Métricas de clasificación con desbalance** sin balancear."),
        section(16, "Ejercicios propuestos",
                "1. Implementa LOF (`LocalOutlierFactor`) y compara.\n"
                "2. Añade SHAP a IF para explicar 5 fallos.\n"
                "3. Ajusta `contamination` y observa el efecto."),
        section(17, "Cómo se reutiliza con datos reales",
                "Re-entrenar mensualmente con los datos del último mes (drift). El "
                "pipeline mismo no cambia."),
        common_summary(next_notebook="03_case_C_hvac_anomaly_detection/05_validacion_fallos_etiquetados.ipynb",
                       docs_link="docs/validation/ml-validation.md"),
    ]
    return emit(target=target, rel_path="03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder.ipynb",
                title=title, case=CASE, layer="oro", spec=SPEC, sections=sections)


def _val(target: Path) -> Path:
    title = "Caso C · 05 Validación supervisada con etiquetas — matriz por tipo"
    sections = [
        section(1, "Objetivo",
                "Reportar precision, recall y F1 por tipo de fallo, no solo AUC global."),
        section(2, "Qué se aprende",
                "- Reportes desglosados.\n"
                "- Trade-off precision vs recall.\n"
                "- Cómo escoger umbral según coste de FN."),
        section(3, "Contexto del caso de uso",
                "En CENTINELA+ un FN (no detectar) es peor que un FP (alarma falsa). "
                "Tunear umbral con eso en mente."),
        section(4, "Relación con CENTINELA+", "Validación final antes de servir el modelo."),
        section(5, "Relación con Medallion", "Oro."),
        section(6, "Datos de entrada", "Mock + scores del notebook anterior."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(9, "Carga de datos o mock", "Recomputamos rápidamente.",
                """\
df, _ = mocks.make_lbnl_fdd_rtu_mock()
X = pd.DataFrame({
    "dt_supply_return": df["RA_TEMP"] - df["SA_TEMP"],
    "valve": df["CCV"], "fan": df["FAN_STATE"],
}).dropna()
y = df["is_fault"].astype(int).iloc[X.index]
ftype = df["fault_type"].iloc[X.index]
"""),
        section(10, "Exploración paso a paso", "Train IF rápido (clase).",
                """\
from sklearn.ensemble import IsolationForest
iso = IsolationForest(contamination=0.15, random_state=SEED).fit(X)
score = -iso.score_samples(X)
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro",
                "Threshold por percentil 90.",
                """\
import numpy as np
threshold = np.percentile(score, 90)
y_pred = (score >= threshold).astype(int)
print(f"threshold={threshold:.3f}; predicted positives={y_pred.sum()}")
"""),
        section(13, "Visualizaciones explicativas",
                "Tabla precision/recall por tipo.",
                """\
from sklearn.metrics import precision_score, recall_score, f1_score
rows = []
for t in ftype.unique():
    if t == "normal":
        continue
    mask = (ftype == t) | (ftype == "normal")
    yt = (ftype[mask] == t).astype(int)
    yp = y_pred[mask]
    rows.append({
        "fault": t,
        "precision": precision_score(yt, yp, zero_division=0),
        "recall": recall_score(yt, yp, zero_division=0),
        "f1": f1_score(yt, yp, zero_division=0),
        "support": int(yt.sum()),
    })
report = pd.DataFrame(rows).set_index("fault").round(3)
report
"""),
        section(14, "Validaciones",
                "Recall por tipo no debe ser cero (sería detector ciego).",
                """\
assert (report["recall"] > 0.05).all()
"""),
        section(15, "Errores comunes",
                "1. Reportar solo macro F1 — esconde tipos raros.\n"
                "2. Comparar threshold % sin recalibrar entre runs.\n"
                "3. Mezclar período de entrenamiento con período de evaluación."),
        section(16, "Ejercicios propuestos",
                "1. Calcula la matriz de confusión cruzada.\n"
                "2. Aplica `class_weight` en un modelo supervisado RF y compara.\n"
                "3. Diseña una métrica con coste asimétrico (FN cuesta 5x FP)."),
        section(17, "Cómo se reutiliza con datos reales",
                "Cuando llegue un ticket en producción, evaluar precision/recall/F1 sobre la "
                "ventana etiquetada. Re-entrenar si recall < 0.7."),
        common_summary(next_notebook="04_case_D_iaq_occupancy/01_eda_iaq_ocupacion.ipynb",
                       docs_link="docs/validation/ml-validation.md"),
    ]
    return emit(target=target, rel_path="03_case_C_hvac_anomaly_detection/05_validacion_fallos_etiquetados.ipynb",
                title=title, case=CASE, layer="oro", spec=SPEC, sections=sections)


def build(target: Path) -> int:
    _eda(target)
    _bronze_silver(target)
    _features(target)
    _models(target)
    _val(target)
    return 5
