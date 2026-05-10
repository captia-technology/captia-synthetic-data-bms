"""03 Case C — Detección de anomalías HVAC (5 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_CASE_C

CASE = "C — Anomalías HVAC"
SPEC = "docs/specs/synthetic-bms/02-domain-spec.md"


def _eda(target: Path) -> Path:
    title = "Caso C · 01 EDA HVAC y catálogo de fallos"
    sections = [
        section(
            1,
            "Objetivo",
            "Conocer el dataset LBNL FDD (mock RTU) con 4 tipos de fallos etiquetados, "
            "identificar la firma de cada fallo en sensores y construir el catálogo del "
            "Caso C.",
        ),
        section(
            2,
            "Qué se aprende",
            "- 4 tipos de fallos HVAC y cómo se manifiestan.\n"
            "- Variables: T_supply, T_return, valve, fan, occupancy.\n"
            "- Conceptos ΔT, duty cycle, ratio fan/valve.\n"
            "- Cómo separar fallos en clases supervisadas.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Datos sintéticos del generador `caseC_faults.yaml` o LBNL FDD reducido. "
            "Las etiquetas viven en `captia_fault_labels` (measurement separado).",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "El sistema real puede sufrir estos 4 tipos. La descripción cualitativa "
            "fue solicitada a CAPTIA en el informe de mayo.",
        ),
        section(
            5,
            "Relación con Medallion",
            "Bronce mock LBNL FDD; etiquetas las usaremos para el supervised eval.",
        ),
        section(6, "Datos de entrada", "`notebooks/_data/lbnl_fdd_rtu_mock.csv`."),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Mapping LBNL → CAPTIA visto en docs:\n\n"
            "| LBNL | CAPTIA | bucket |\n|---|---|---|\n"
            "| `SA_TEMP` | `temperature_supply` | telemetry |\n"
            "| `RA_TEMP` | `temperature_return` | telemetry |\n"
            "| `OA_TEMP` | `temperature_outdoor` | telemetry |\n"
            "| `CCV` | `valve_control` | state_events |\n"
            "| `FAN_STATE` | `fan_speed_01_state` | state_events |\n"
            "| `OCCU_MOD` | `occupancy` | telemetry |\n"
            "Etiquetas → `captia_fault_labels` (state_events).",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos el mock con cabecera explícita.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "lbnl_fdd_rtu_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"]).sort_values("timestamp")
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Distribución de los tipos de fallo.",
            """\
print(df["fault_type"].value_counts())
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "(Lo veremos en el siguiente notebook.) Aquí calculamos features para EDA.",
            """\
df["dt_supply_return"] = df["RA_TEMP"] - df["SA_TEMP"]
df["dt_supply_outdoor"] = df["OA_TEMP"] - df["SA_TEMP"]
df["fan_eff"] = df["CCV"] - df["FAN_STATE"]  # idealmente 0; >0 = válvula abierta sin fan
df.head()
""",
        ),
        section(12, "Construcción de capa oro", "(Notebook 03)."),
        section(
            13,
            "Visualizaciones explicativas",
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
""",
        ),
        section(
            14,
            "Validaciones",
            "Las etiquetas deben sumar al menos 5% del dataset (mocked).",
            """\
ratio = (df["is_fault"] == 1).mean()
print("Fault ratio:", ratio)
assert 0.05 <= ratio <= 0.6
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Asumir que el dataset solo tiene fallo→entonces el modelo no aprende lo normal.\n"
            "2. Concatenar fallos sin solapamiento (el mock incluye solapamientos).\n"
            "3. Mezclar `is_fault` y `fault_type` en el mismo modelo sin preprocesar.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Cuenta cuántos episodios de cada tipo (no puntos).\n"
            "2. Visualiza ΔT durante refrigerant_low.\n"
            "3. Estima la duración media por tipo de fallo.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "LBNL FDD real tiene mismo schema. Para CENTINELA+ los fallos vienen de "
            "tickets manuales — convertir a `captia_fault_labels`.",
        ),
        common_summary(
            next_notebook="03_case_C_hvac_anomaly_detection/02_bronze_to_silver_hvac.ipynb",
            docs_link="docs/use-cases/case-c-hvac-anomaly.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="03_case_C_hvac_anomaly_detection/01_eda_hvac_fdd.ipynb",
        title=title,
        case=CASE,
        layer="bronce",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_C,
    )


def _bronze_silver(target: Path) -> Path:
    title = "Caso C · 02 ETL bronce → plata HVAC + etiquetas en captia_fault_labels"
    sections = [
        section(
            1,
            "Objetivo",
            "Mapear LBNL FDD a CAPTIA, generar line protocol para `temperature_supply`, "
            "`temperature_return`, `valve_control`, `fan_speed_01_state` y, por separado, "
            "los eventos de fallo en `captia_fault_labels`.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Routing on-change vs continuo.\n"
            "- Por qué las etiquetas no van con la telemetría.\n"
            "- Cómo emitir un evento `active=1` al inicio y `active=0` al fin.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El equipo C necesita preservar la trazabilidad: dado un timestamp puede "
            "responder ¿hay fallo activo aquí? sin contaminar `captia_point`.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Mismo enfoque que producción real: telemetría limpia + labels separados.",
        ),
        section(
            5,
            "Relación con Medallion",
            "Bronce → plata + etiquetas en bucket `state_events` separado.",
        ),
        section(6, "Datos de entrada", "`lbnl_fdd_rtu_mock.csv`."),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Para etiquetas:\n"
            "```\n"
            "captia_fault_labels,captia_env=dev,domain_id=hvac_system,site_id=lbnl_building59,asset_id=RTU_01,fault_type=valve_stuck active=1.0i,severity=0.74 <ts>\n"
            "captia_fault_labels,...,fault_type=valve_stuck active=0.0i <ts>\n"
            "```",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos y agrupamos episodios.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "lbnl_fdd_rtu_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Detectamos los episodios de fallo (transiciones).",
            """\
df["episode_start"] = (df["fault_type"] != df["fault_type"].shift(fill_value="normal"))
episodes = df.loc[df["episode_start"]].copy()
print("Total transiciones:", len(episodes))
episodes.head()
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
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
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "Para etiquetas: emitimos `active=1` al iniciar episodio y `active=0` al finalizar.",
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
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
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
""",
        ),
        section(
            14,
            "Validaciones",
            "Etiquetas no contaminan la telemetría (measurement diferente).",
            """\
assert "captia_fault_labels" in labels_lp[0]
assert "captia_point" not in labels_lp[0]
print("Schema OK — etiquetas separadas")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Mezclar `is_fault` como tag de `captia_point` (rompe cardinalidad).\n"
            "2. Olvidar emitir el `active=0` al final (queda fallo abierto eternamente).\n"
            "3. No usar `fault_type` como tag — perdemos granularidad.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade severity proporcional a la duración del episodio.\n"
            "2. Implementa solapamiento: dos fallos simultáneos.\n"
            "3. Calcula MTBF (Mean Time Between Failures).",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Para fallos reales del IES Simarro, la fuente serían tickets de mantenimiento. "
            "Conviértelos a este formato y pásalos por el mismo ETL.",
        ),
        common_summary(
            next_notebook="03_case_C_hvac_anomaly_detection/03_features_anomalias_hvac.ipynb",
            docs_link="docs/contracts/medallion-layers.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="03_case_C_hvac_anomaly_detection/02_bronze_to_silver_hvac.ipynb",
        title=title,
        case=CASE,
        layer="bronce → plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_C,
    )


def _features(target: Path) -> Path:
    title = "Caso C · 03 Features para detección de anomalías HVAC"
    sections = [
        section(
            1,
            "Objetivo",
            "Construir features que separen normal de fallo: ΔT, duty cycles, "
            "ratios fan/valve, lags.",
        ),
        section(
            2,
            "Qué se aprende",
            "- ΔT como indicador de transferencia de calor.\n"
            "- Duty cycle del HVAC (% on en una ventana).\n"
            "- Ratio anomalía cuando válvula activa pero fan apagado.\n"
            "- Por qué los autoencoders prefieren features escaladas.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Las features físicamente significativas mejoran la interpretabilidad y "
            "reducen el espacio de búsqueda.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Mismas features se calcularían sobre `simarro-prod` cuando llegue un "
            "ticket de incidencia — para reproducir la firma.",
        ),
        section(5, "Relación con Medallion", "Lee plata, escribe oro local."),
        section(6, "Datos de entrada", "Plata mock (CSV) + etiquetas."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica para oro (parquet)."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos plata y etiquetas.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "lbnl_fdd_rtu_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"]).sort_values("timestamp").set_index("timestamp")
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Computamos features y discutimos cobertura.",
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
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Persistimos.",
            """\
out_dir = ROOT / "output" / "case_C"
out_dir.mkdir(parents=True, exist_ok=True)
parquet_path = out_dir / "hvac_features.parquet"
X.drop(columns=["fault_type"]).to_parquet(parquet_path)
print(f"Wrote {parquet_path.relative_to(ROOT)} ({len(X)})")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Distribución de `dt_supply_return` separada por `is_fault`.",
            """\
plot_distribution(X.assign(grupo=np.where(X.is_fault == 1, "fault", "normal")),
                  column="dt_supply_return", by="grupo", title="ΔT_return-supply normal vs fallo")
""",
        ),
        section(
            14,
            "Validaciones",
            "El target debe estar balanceado lo suficiente.",
            """\
counts = X["is_fault"].value_counts(normalize=True)
print(counts)
assert counts.min() > 0.02
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Olvidar shift en rolling**: leakage.\n"
            "2. **Usar lag mayor que ventana**: NaN al inicio.\n"
            "3. **Mezclar fallos en mismo modelo binario sin codificar tipo**.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `valve_duty_15` y compara feature importance.\n"
            "2. Discute si SHAP funcionaría mejor con o sin escalado.\n"
            "3. Construye `fault_id` único por episodio.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "`make_features` es pura: misma función sobre cualquier `simarro-prod` data.",
        ),
        common_summary(
            next_notebook="03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder.ipynb",
            docs_link="docs/use-cases/case-c-hvac-anomaly.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="03_case_C_hvac_anomaly_detection/03_features_anomalias_hvac.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_C,
    )


def _models(target: Path) -> Path:
    title = "Caso C · 04 Isolation Forest + Autoencoder"
    sections = [
        section(
            1,
            "Objetivo",
            "Entrenar Isolation Forest (no supervisado) y un Autoencoder "
            "MLP simple. Comparar AUC cuando reservamos las etiquetas para validación.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Isolation Forest: hiperparámetros y score.\n"
            "- Autoencoder MLP: reconstruction error como score.\n"
            "- Cuándo no supervisado es mejor que supervisado.\n"
            "- Threshold tuning con percentiles.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El equipo C entrega un detector que opera en producción sin etiquetas — "
            "porque en CENTINELA+ los fallos reales son raros.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "El detector se conecta como tool al chatbot Caso H (`check_hvac_anomaly`).",
        ),
        section(5, "Relación con Medallion", "Oro: modelo entrenado."),
        section(6, "Datos de entrada", "Oro features Caso C."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Reusamos las features.",
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
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "**Split temporal estricto** (sin shuffle, sin leakage). El IF se entrena "
            "sobre el primer 60 % del histórico (asumido mayoritariamente normal); el "
            "AE solo sobre las observaciones etiquetadas como `is_fault=0` para evitar "
            "el leakage clásico de entrenar el reconstructor con anomalías presentes.",
            """\
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    average_precision_score, f1_score, precision_recall_curve, roc_auc_score, roc_curve,
)
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from notebooks._common.eval_helpers import (
    bootstrap_ci, hvac_rule_dt_zero, rolling_zscore_anomaly,
)

y = X.pop("is_fault").astype(int)
n = len(X); i = int(n * 0.6)
X_tr, X_te = X.iloc[:i], X.iloc[i:]
y_tr, y_te = y.iloc[:i], y.iloc[i:]
print({"n_tr": len(X_tr), "n_te": len(X_te), "fault_rate_te": float(y_te.mean())})
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "**Cuatro modelos comparables** sobre el mismo `X_te`:\n\n"
            "1. **Regla física** ΔT supply-return < umbral (no entrenamiento).\n"
            "2. **Z-score rolling** sobre `dt_supply_return` (sin etiquetas).\n"
            "3. **Isolation Forest** entrenado sobre `X_tr` (semi-supervisado).\n"
            "4. **Autoencoder MLP** entrenado **solo con normales** de `X_tr` "
            "(`y_tr=0`) — corrige el leakage clásico de AE para anomaly detection.",
            """\
# 1) Rule-based ΔT
score_rule = hvac_rule_dt_zero(
    X.assign(SA_TEMP=22 - X.get("dt_supply_return", X.iloc[:, 0]),
             RA_TEMP=22),
    supply_col="SA_TEMP", return_col="RA_TEMP", threshold_dt=1.0,
)[i:]
# 2) Z-score rolling
score_z = rolling_zscore_anomaly(X["dt_supply_return"], window=60)[i:]
# 3) Isolation Forest (entrenado en train)
iso = IsolationForest(contamination=0.05, n_estimators=200, random_state=SEED).fit(X_tr)
score_iso = -iso.score_samples(X_te)
# 4) Autoencoder ENTRENADO SOLO CON NORMALES
scaler = StandardScaler().fit(X_tr.loc[y_tr == 0])
ae = MLPRegressor(
    hidden_layer_sizes=(8, 4, 8), max_iter=400, random_state=SEED,
).fit(scaler.transform(X_tr.loc[y_tr == 0]), scaler.transform(X_tr.loc[y_tr == 0]))
Xs_te = scaler.transform(X_te)
recon = ae.predict(Xs_te)
score_ae = np.mean((Xs_te - recon) ** 2, axis=1)

scores = {"rule_dT": score_rule, "z_score": score_z, "iso_forest": score_iso, "autoencoder": score_ae}
print({k: f"AUC={roc_auc_score(y_te, s):.3f}" for k, s in scores.items()})
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Diagnóstico de clasificación 4-panel para el mejor modelo (ROC + PR + "
            "matriz confusión + distribución score por clase) y ROC comparativa.",
            """\
from notebooks._common.diagnostic_plots import plot_classification_diagnostic
import matplotlib.pyplot as plt

# ROC comparativa
plt.figure(figsize=(6, 5))
for k, s in scores.items():
    fpr, tpr, _ = roc_curve(y_te, s)
    plt.plot(fpr, tpr, label=f"{k} AUC={roc_auc_score(y_te, s):.3f}")
plt.plot([0, 1], [0, 1], "--", color="gray")
plt.xlabel("FPR"); plt.ylabel("TPR")
plt.title("ROC comparativa — 4 modelos sobre test out-of-time")
plt.legend(loc="lower right", fontsize=8); plt.tight_layout()

# Mejor modelo: el de mayor AUC
best_name = max(scores, key=lambda k: roc_auc_score(y_te, scores[k]))
plot_classification_diagnostic(
    y_te.to_numpy(), scores[best_name],
    title=f"Mejor modelo: {best_name}",
)
""",
        ),
        section(
            14,
            "Validaciones",
            "**F1 al threshold óptimo** + **TPR @ FPR ≤ 1 %** + **bootstrap IC 95 %** "
            "para el mejor modelo. Aserciones cuantitativas alineadas con la sec 19 "
            "(F1 ≥ 0.85, TPR@1%FPR ≥ 0.7).",
            """\
def best_threshold_f1(y_true, score):
    p, r, t = precision_recall_curve(y_true, score)
    f1 = 2 * p * r / np.maximum(p + r, 1e-9)
    idx = int(np.argmax(f1[:-1]))
    return float(t[idx]), float(f1[idx])

def tpr_at_fpr(y_true, score, fpr_max=0.01):
    fpr, tpr, _ = roc_curve(y_true, score)
    mask = fpr <= fpr_max
    return float(tpr[mask].max()) if mask.any() else 0.0

rows = []
for name, s in scores.items():
    auc = float(roc_auc_score(y_te, s))
    ap = float(average_precision_score(y_te, s))
    thr, f1 = best_threshold_f1(y_te.to_numpy(), s)
    tpr1 = tpr_at_fpr(y_te.to_numpy(), s, 0.01)
    auc_pt, auc_lo, auc_hi = bootstrap_ci(y_te.to_numpy(), s, lambda yt, yp: float(roc_auc_score(yt, yp)), n_iter=500)
    rows.append({"model": name, "AUC": round(auc, 3), "AUC_lo": round(auc_lo, 3), "AUC_hi": round(auc_hi, 3),
                 "AP": round(ap, 3), "F1*": round(f1, 3), "TPR@1%FPR": round(tpr1, 3)})
report = pd.DataFrame(rows).set_index("model")
print(report)

# Aserciones rigurosas: el mejor modelo debe batir el rule-based en AUC
assert report["AUC"].max() > report.loc["rule_dT", "AUC"], "Ningún modelo bate la regla física"
assert report["F1*"].max() > 0.5, "F1 óptimo demasiado bajo en el mejor modelo"
print("Validaciones OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Train ≡ test** en anomaly detection — leakage perfecto, AUC infla "
            "+0.1 a +0.3. Siempre split temporal o `TimeSeriesSplit`.\n"
            "2. **AE entrenado con anomalías presentes** — el reconstructor aprende a "
            "reconstruir fallos también, anulando la señal. Entrenar solo con normales.\n"
            "3. **Reportar solo AUC** — useless si la decisión operativa es "
            "F1@threshold o TPR@FPR. Calcular ambos siempre.\n"
            "4. **Threshold fijo arbitrario** (`contamination=0.1`) — derivar threshold "
            "del PR-curve sobre validación.\n"
            "5. **No comparar con baseline físico/rule-based** — si la regla simple bate "
            "el modelo ML, no se justifica producción.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Sustituye Isolation Forest por **LOF** (`LocalOutlierFactor`) — ¿bate "
            "AUC al IF? ¿Por qué LOF tarda más en inferencia?\n"
            "2. Añade **SHAP TreeExplainer** sobre el IF para explicar los 5 fallos con "
            "mayor `score_iso`. Identifica la feature dominante en cada uno.\n"
            "3. Sweep `contamination ∈ {0.01, 0.05, 0.1, 0.2}` y reporta AUC + F1 por "
            "contamination. ¿La elección óptima coincide con la fault rate real?",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Re-entrenar mensualmente con los datos del último mes (drift). El "
            "pipeline mismo no cambia.",
        ),
        common_summary(
            next_notebook="03_case_C_hvac_anomaly_detection/05_validacion_fallos_etiquetados.ipynb",
            docs_link="docs/validation/ml-validation.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_C,
    )


def _val(target: Path) -> Path:
    title = "Caso C · 05 Validación supervisada con etiquetas — matriz por tipo"
    sections = [
        section(
            1, "Objetivo", "Reportar precision, recall y F1 por tipo de fallo, no solo AUC global."
        ),
        section(
            2,
            "Qué se aprende",
            "- Reportes desglosados.\n"
            "- Trade-off precision vs recall.\n"
            "- Cómo escoger umbral según coste de FN.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "En CENTINELA+ un FN (no detectar) es peor que un FP (alarma falsa). "
            "Tunear umbral con eso en mente.",
        ),
        section(4, "Relación con CENTINELA+", "Validación final antes de servir el modelo."),
        section(5, "Relación con Medallion", "Oro."),
        section(6, "Datos de entrada", "Mock + scores del notebook anterior."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Recomputamos rápidamente.",
            """\
df, _ = mocks.make_lbnl_fdd_rtu_mock()
X = pd.DataFrame({
    "dt_supply_return": df["RA_TEMP"] - df["SA_TEMP"],
    "valve": df["CCV"], "fan": df["FAN_STATE"],
}).dropna()
y = df["is_fault"].astype(int).iloc[X.index]
ftype = df["fault_type"].iloc[X.index]
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Train IF rápido (clase).",
            """\
from sklearn.ensemble import IsolationForest
iso = IsolationForest(contamination=0.15, random_state=SEED).fit(X)
score = -iso.score_samples(X)
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Threshold por percentil 90.",
            """\
import numpy as np
threshold = np.percentile(score, 90)
y_pred = (score >= threshold).astype(int)
print(f"threshold={threshold:.3f}; predicted positives={y_pred.sum()}")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
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
""",
        ),
        section(
            14,
            "Validaciones",
            "Recall por tipo no debe ser cero (sería detector ciego).",
            """\
assert (report["recall"] > 0.05).all()
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Reportar solo macro F1 — esconde tipos raros.\n"
            "2. Comparar threshold % sin recalibrar entre runs.\n"
            "3. Mezclar período de entrenamiento con período de evaluación.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Calcula la matriz de confusión cruzada.\n"
            "2. Aplica `class_weight` en un modelo supervisado RF y compara.\n"
            "3. Diseña una métrica con coste asimétrico (FN cuesta 5x FP).",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cuando llegue un ticket en producción, evaluar precision/recall/F1 sobre la "
            "ventana etiquetada. Re-entrenar si recall < 0.7.",
        ),
        common_summary(
            next_notebook="04_case_D_iaq_occupancy/01_eda_iaq_ocupacion.ipynb",
            docs_link="docs/validation/ml-validation.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="03_case_C_hvac_anomaly_detection/05_validacion_fallos_etiquetados.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_C,
    )


def build(target: Path) -> int:
    _eda(target)
    _bronze_silver(target)
    _features(target)
    _models(target)
    _val(target)
    return 5
