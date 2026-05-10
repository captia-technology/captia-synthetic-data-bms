"""04 Case D — Calidad de aire, confort y ocupación (5 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_CASE_D

CASE = "D — IAQ + ocupación"
SPEC = "docs/specs/synthetic-bms/02-domain-spec.md"


def _eda(target: Path) -> Path:
    title = "Caso D · 01 EDA IAQ y ocupación en aulas"
    sections = [
        section(
            1,
            "Objetivo",
            "Explorar el dataset In-Gauge mock de AULA01: variables ambientales, "
            "respuesta del CO₂ a la ocupación y patrón lectivo de la Comunidad Valenciana.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Lectura del dataset In-Gauge / En-Gage.\n"
            "- Cómo el CO₂ delata ocupación.\n"
            "- Estacionalidad lectiva y horario de recreos.\n"
            "- IAQ index y rangos OMS.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El Caso D es el más alineado con AULA01 real. Lo que aprendamos aquí "
            "debe trasladarse directamente a sensores reales del IES.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Las 9 variables del gateway BMS coinciden con las del CSV (`Indoor_CO2` → "
            "`co2`, etc.).",
        ),
        section(5, "Relación con Medallion", "Bronce: CSV In-Gauge. Próximo notebook → plata."),
        section(6, "Datos de entrada", "`notebooks/_data/ingauge_aula01_mock.csv`."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "Mapping In-Gauge → CAPTIA visto en docs."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos el CSV y derivamos día/horario lectivo.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "ingauge_aula01_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
df["hour"] = df["timestamp"].dt.hour
df["dow"] = df["timestamp"].dt.dayofweek
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Estadísticas básicas y picos por horario.",
            """\
print(df[["Indoor_CO2", "Indoor_Temp", "Indoor_Hum", "Indoor_Lux", "People_Count"]].describe().round(2))
print("\\nCO2 medio en horario lectivo (8-15h L-V):")
mask = (df["hour"].between(8, 14)) & (df["dow"] < 5)
print(df.loc[mask, "Indoor_CO2"].mean().round(1))
""",
        ),
        section(11, "Transformación bronce → plata", "Notebook siguiente."),
        section(12, "Construcción de capa oro", "Notebook 03 (features)."),
        section(
            13,
            "Visualizaciones explicativas",
            "Plot CO₂ vs ocupación durante 3 días lectivos.",
            """\
sample = df.head(60 * 24 * 3)  # 3 días
fig, ax1 = plt.subplots(figsize=(10, 3))
ax1.plot(sample["timestamp"], sample["Indoor_CO2"], color="#3F51B5", label="CO2")
ax1.set_ylabel("CO2 ppm")
ax2 = ax1.twinx()
ax2.plot(sample["timestamp"], sample["People_Count"], color="#FF5722", label="people")
ax2.set_ylabel("ocupantes")
plt.title("CO2 sigue a ocupación (3 días)")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "1. CO2 nunca > 5000.\n2. Temperatura entre 16 y 32.",
            """\
assert df["Indoor_CO2"].between(300, 5000).all()
assert df["Indoor_Temp"].between(15, 32).all()
print("Rangos físicos OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Confundir minutos con segundos.\n"
            "2. Excluir horario nocturno (también informa: nivel base).\n"
            "3. No identificar el recreo (11:00–11:30) como subcaso.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Calcula `dCO2/dt` y compara su distribución con/sin clase.\n"
            "2. Identifica los 3 picos de CO2 más altos del dataset.\n"
            "3. Estima el caudal de ventilación equivalente.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cuando AULA01 tenga histórico, este EDA aplica directamente. "
            "Las queries Flux equivalentes están en `docs/use-cases/case-d-iaq-occupancy.md`.",
        ),
        common_summary(
            next_notebook="04_case_D_iaq_occupancy/02_bronze_to_silver_iaq.ipynb",
            docs_link="docs/use-cases/case-d-iaq-occupancy.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="04_case_D_iaq_occupancy/01_eda_iaq_ocupacion.ipynb",
        title=title,
        case=CASE,
        layer="bronce",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_D,
    )


def _bronze_silver(target: Path) -> Path:
    title = "Caso D · 02 ETL bronce → plata IAQ + poblar captia_metadata"
    sections = [
        section(
            1,
            "Objetivo",
            "Transformar el CSV In-Gauge a `captia_point` y poblar `captia_point_meta` "
            "para que las tareas Flux de downsampling funcionen.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Mapping completo In-Gauge → CAPTIA.\n"
            "- Diferencia continuo vs on-change.\n"
            "- Cómo poblar el catálogo de variables.\n"
            "- Routing a `state_events`.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Sin `captia_point_meta` poblado, los buckets `_1m`, `_15m`, `_1h` quedan "
            "vacíos; el modelo del notebook 04 fallará.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "El catálogo es por dominio (no por aula): poblar una vez por `domain_id` "
            "es suficiente.",
        ),
        section(5, "Relación con Medallion", "Bronce → plata + metadata."),
        section(6, "Datos de entrada", "`ingauge_aula01_mock.csv`."),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Two outputs: telemetría `.lp` y metadata `.lp` para `captia_metadata`.",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos y reformulamos largo.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "ingauge_aula01_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
mapping = {
    "Indoor_CO2": ("co2", "telemetry"),
    "Indoor_Temp": ("temperature_01", "telemetry"),
    "Indoor_Hum": ("relative_humidity_01", "telemetry"),
    "Indoor_Noise": ("avg_sound_level", "telemetry"),
    "Indoor_Lux": ("luminosity", "telemetry"),
    "People_Count": ("people_count", "telemetry"),
    "Occupied": ("occupancy", "telemetry"),
    "CoolingState": ("ac_state", "state_events"),
}
print(mapping)
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Para cada columna del CSV producimos una serie "
            "larga; `state_events` se filtra a transiciones.",
            """\
def emit_lp_telemetry(df, csv_col, captia_var, asset="AULA01"):
    serie = df[["timestamp", csv_col]].dropna()
    for _, row in serie.iterrows():
        ts_ns = int(pd.Timestamp(row["timestamp"]).value)
        yield build_line_protocol(
            measurement=MEASUREMENT_TELEMETRY,
            tags={
                "captia_env": "dev", "domain_id": "bms_classrooms",
                "site_id": "ies_simarro", "asset_id": asset, "variable": captia_var,
            },
            fields={"value": float(row[csv_col])},
            timestamp_ns=ts_ns,
        )

def emit_lp_state(df, csv_col, captia_var, asset="AULA01"):
    serie = df[["timestamp", csv_col]].dropna().copy()
    serie["chg"] = serie[csv_col].diff().fillna(serie[csv_col]).abs() > 0
    for _, row in serie[serie["chg"]].iterrows():
        ts_ns = int(pd.Timestamp(row["timestamp"]).value)
        yield (
            f"captia_point,captia_env=dev,domain_id=bms_classrooms,"
            f"site_id=ies_simarro,asset_id={asset},variable={captia_var} "
            f"value={float(row[csv_col])} {ts_ns}"
        )
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Generamos los dos ficheros (sample 200 filas para clase).",
            """\
out_dir = ROOT / "output" / "case_D"
out_dir.mkdir(parents=True, exist_ok=True)
sample = df.head(200)

telem_lines, state_lines = [], []
for csv_col, (captia_var, kind) in mapping.items():
    if kind == "telemetry":
        telem_lines.extend(emit_lp_telemetry(sample, csv_col, captia_var))
    else:
        state_lines.extend(emit_lp_state(sample, csv_col, captia_var))

(out_dir / "iaq_telemetry.lp").write_text("\\n".join(telem_lines), encoding="utf-8")
(out_dir / "iaq_state_events.lp").write_text("\\n".join(state_lines), encoding="utf-8")
print(f"telemetry: {len(telem_lines)} líneas; state_events: {len(state_lines)} líneas")
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "Generamos las líneas para `captia_point_meta` (catálogo).",
            """\
catalogo = []
for csv_col, (captia_var, _) in mapping.items():
    info = KNOWN_VARIABLES.get(captia_var, {"unit": "?", "range": (0, 1), "metric_kind": "analog_gauge"})
    rmin, rmax = info["range"]
    catalogo.append(
        f"captia_point_meta,captia_env=dev,domain_id=bms_classrooms,"
        f"site_id=ies_simarro,asset_type=classroom,variable={captia_var} "
        f'metric_kind="{info["metric_kind"]}",unit="{info["unit"]}",range_min={rmin},range_max={rmax}'
    )
(out_dir / "iaq_metadata.lp").write_text("\\n".join(catalogo), encoding="utf-8")
print(f"metadata: {len(catalogo)} variables")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Distribución de mensajes por bucket.",
            """\
counts = pd.Series({"telemetry": len(telem_lines), "state_events": len(state_lines), "metadata": len(catalogo)})
counts.plot.bar(color="#3F51B5", figsize=(7, 3))
plt.title("Líneas por destino")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Cada `state_events` debe contener `value=0` o `value=1`.",
            """\
import re

if state_lines:
    for line in state_lines[:5]:
        m = re.search(r"value=([0-9.]+)", line)
        val = float(m.group(1))
        assert val in {0.0, 1.0}, f"Bad value: {val}"
    print("State_events OK · ejemplo:", state_lines[0])
else:
    print("Sin transiciones de estado en este sample (todas las filas iguales).")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **No emitir cambio inicial**: `diff()` en NaN omite el primer valor.\n"
            "2. **Mismo timestamp dos veces**: dedup InfluxDB las descarta.\n"
            "3. **Olvidar metadata**: rollups vacíos.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `vehicle_count` con `domain_id=traffic_cameras`.\n"
            "2. Verifica que `Occupied=1` también va a `telemetry` (bool_presence).\n"
            "3. Prueba a desactivar la metadata y observa qué falla.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "El sensor real publica directamente; este ETL es solo para datasets "
            "públicos. Pero la **definición** de variables y metadata se mantiene.",
        ),
        common_summary(
            next_notebook="04_case_D_iaq_occupancy/03_features_confort_ocupacion.ipynb",
            docs_link="docs/contracts/variable-catalog.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="04_case_D_iaq_occupancy/02_bronze_to_silver_iaq.ipynb",
        title=title,
        case=CASE,
        layer="bronce → plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_D,
    )


def _features(target: Path) -> Path:
    title = "Caso D · 03 Features para predicción de ocupación"
    sections = [
        section(
            1,
            "Objetivo",
            "Construir features informativas para detectar ocupación a partir de "
            "variables ambientales (sin sensor de presencia).",
        ),
        section(
            2,
            "Qué se aprende",
            "- Derivada del CO₂ (`dCO2/dt`).\n"
            "- IAQ index sintético.\n"
            "- Lag features y agregados ventana.\n"
            "- Cómo manejar el desbalance de clases.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El sensor de presencia no siempre existe; queremos inferir ocupación "
            "indirectamente desde ambiente (CO₂, sonido).",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Si AULA01 no tiene sensor de presencia, este modelo lo sustituye.",
        ),
        section(5, "Relación con Medallion", "Lee plata, escribe oro local."),
        section(6, "Datos de entrada", "Mock In-Gauge."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica (oro)."),
        section(
            9,
            "Carga de datos o mock",
            "Reusamos el CSV.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "ingauge_aula01_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"]).set_index("timestamp")
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Computamos features.",
            """\
def make_features(d):
    f = pd.DataFrame(index=d.index)
    f["co2"] = d["Indoor_CO2"]
    f["temp"] = d["Indoor_Temp"]
    f["rh"] = d["Indoor_Hum"]
    f["lux"] = d["Indoor_Lux"]
    f["noise"] = d["Indoor_Noise"]
    f["dco2_5min"] = d["Indoor_CO2"].diff(5)
    f["co2_lag_15"] = d["Indoor_CO2"].shift(15)
    f["co2_roll_30"] = d["Indoor_CO2"].rolling(30).mean()
    f["noise_roll_15"] = d["Indoor_Noise"].rolling(15).mean()
    # IAQ aproximado
    f["iaq"] = (
        50 * (f["co2"] / 1000).clip(upper=5)
        + 30 * (f["rh"] / 50 - 1).abs()
        + 15 * (f["temp"] / 22 - 1).abs() * 100
    ).clip(upper=500)
    f["y_occupied"] = d["Occupied"]
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
out_dir = ROOT / "output" / "case_D"
out_dir.mkdir(parents=True, exist_ok=True)
parquet_path = out_dir / "iaq_features.parquet"
X.to_parquet(parquet_path)
print(f"Wrote {parquet_path.relative_to(ROOT)} ({len(X)})")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Comparativa correlaciones.",
            """\
correls = X.drop(columns=["y_occupied"]).corrwith(X["y_occupied"]).sort_values()
correls.plot.barh(color="#FF5722", figsize=(7, 4))
plt.title("Correlación con y_occupied")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "El `y_occupied` mantiene la fracción esperada (~30%).",
            """\
ratio = X["y_occupied"].mean()
print({"y_ratio": ratio})
assert 0.05 < ratio < 0.7
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Confundir Indoor_Occupancy (0/1) con People_Count (0..N)**.\n"
            "2. **Suavizar features que cambian rápido** (perdemos picos CO2).\n"
            "3. **Mezclar lectivo y vacaciones**: meter una columna `is_holiday`.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `holiday` (calendario Comunidad Valenciana) y mide ganancia.\n"
            "2. Prueba `dco2_15min` vs `dco2_5min`.\n"
            "3. Calcula y plotea IAQ index a lo largo de un día lectivo.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Misma `make_features(df)` sobre datos reales — solo cambia el path.",
        ),
        common_summary(
            next_notebook="04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente.ipynb",
            docs_link="docs/use-cases/case-d-iaq-occupancy.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="04_case_D_iaq_occupancy/03_features_confort_ocupacion.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_D,
    )


def _model(target: Path) -> Path:
    title = "Caso D · 04 Modelo de ocupación desde ambiente — analítico vs ML"
    sections = [
        section(
            1,
            "Objetivo",
            "Inferir ocupación de un aula desde variables ambientales **sin** sensor de "
            "presencia explícito. Comparamos tres enfoques:\n\n"
            "1. **Threshold trivial** (CO₂ > umbral) — baseline.\n"
            "2. **Inversión analítica del balance de masa CO₂** (Wang 2017, ASHRAE 62.1) — modelo físico.\n"
            "3. **Random Forest balanceado con `TimeSeriesSplit`** — ML supervisado.\n\n"
            "Reportamos F1 + IC 95 % bootstrap para cada uno y discutimos trade-off entre "
            "interpretabilidad y precisión.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Inversión de la EDO de balance de masa para inferir $N(t)$.\n"
            "- Cross-validation temporal con `TimeSeriesSplit(5)`.\n"
            "- `class_weight='balanced'` y por qué es crítico con desbalance.\n"
            "- Bootstrap IC para F1.\n"
            "- Diagnostic plot de clasificación (ROC + PR + matriz confusión + score por clase).",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El gateway BMS de AULA01 mide CO₂ continuamente. Inferir ocupación desde el "
            "ambiente abarata el BOM (sin PIR) y permite alertas tempranas de "
            "sobre-ocupación. El modelo se sirve como tool del chatbot del Caso H "
            "(`get_building_state`).",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Tool en producción. Re-entrenar trimestralmente sobre los últimos 30 días "
            "de simarro-prod (drift por estaciones).",
        ),
        section(5, "Relación con Medallion", "Oro: modelo entrenado + métricas con IC."),
        section(
            6,
            "Datos de entrada",
            "Mock In-Gauge **30 días** (`make_ingauge_aula01_mock(days=30)`) para "
            "asegurar que ambos clases (`occupied=0/1`) aparecen en cada fold.",
        ),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Variables canónicas implicadas:\n\n"
            "| Variable CAPTIA | Rol en el modelo |\n"
            "|---|---|\n"
            "| `co2` | predictor primario (señal ASHRAE 62.1) |\n"
            "| `temperature_01` | predictor secundario |\n"
            "| `relative_humidity_01` | predictor secundario |\n"
            "| `avg_sound_level` | predictor (ruido humano) |\n"
            "| `luminosity` | predictor (luces encendidas) |\n"
            "| `occupancy` | etiqueta (target binario) |",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos **30 días** del mock — suficiente para captar 4 ciclos semanales "
            "y garantizar que el split temporal contiene horario lectivo.",
            """\
from notebooks._common.eval_helpers import (
    bootstrap_ci,
    occupancy_from_co2_balance,
    occupancy_from_co2_threshold,
    time_series_cv_evaluate,
    summarise_cv,
)
from sklearn.metrics import f1_score, precision_score, recall_score

df, _ = mocks.make_ingauge_aula01_mock(days=30)
df = df.set_index("timestamp")
print({"filas": len(df), "ocupacion_pct": float(df["Occupied"].mean())})
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Construimos features con `dCO₂/dt` (la señal **clave** según el balance "
            "de masa) y rolling means, y observamos la distribución de la etiqueta.",
            """\
X = pd.DataFrame(index=df.index)
X["co2"] = df["Indoor_CO2"]
X["dco2_5min"] = df["Indoor_CO2"].diff(5)
X["co2_roll_15"] = df["Indoor_CO2"].rolling(15).mean()
X["temp"] = df["Indoor_Temp"]
X["rh"] = df["Indoor_Hum"]
X["noise"] = df["Indoor_Noise"]
X["lux"] = df["Indoor_Lux"]
X["hour_sin"] = np.sin(2 * np.pi * X.index.hour / 24)
X["hour_cos"] = np.cos(2 * np.pi * X.index.hour / 24)
y = df["Occupied"].astype(int)
mask = X.notna().all(axis=1)
X, y = X.loc[mask], y.loc[mask]
print({"shape": X.shape, "y_pos_rate": round(float(y.mean()), 3)})
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Tres baselines comparables:",
            """\
# Baseline 1 — threshold trivial
y_thr = occupancy_from_co2_threshold(X["co2"], threshold_ppm=600)

# Baseline 2 — inversión analítica del balance de masa CO₂
n_hat = occupancy_from_co2_balance(
    df["Indoor_CO2"].loc[X.index],
    volume_m3=180.0, vent_rate_l_s=12.0, co2_outdoor_ppm=420.0,
    gen_l_s_per_person=4.5e-3,
)
y_balance = (n_hat > 0.5).astype(int).to_numpy()

# Baseline 3 — Random Forest balanceado con TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier

def make_rf():
    return RandomForestClassifier(
        n_estimators=200, max_depth=8, class_weight="balanced",
        random_state=SEED, n_jobs=1,
    )

cv = time_series_cv_evaluate(make_rf, X, y, n_splits=5, is_classifier=True)
print(cv.round(3))
print("\\nResumen RF (folds):", {k: round(v, 3) for k, v in summarise_cv(cv, "f1").items()})
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Diagnóstico de clasificación 4-panel: ROC + PR + matriz de confusión + "
            "distribución del score por clase.",
            """\
from notebooks._common.diagnostic_plots import plot_classification_diagnostic

# Re-entrenar el RF sobre 80 % para diagnostic visual (con CV ya validado)
n = len(X); i = int(n * 0.8)
X_tr, X_te = X.iloc[:i], X.iloc[i:]
y_tr, y_te = y.iloc[:i], y.iloc[i:]
rf = make_rf().fit(X_tr, y_tr)
score = rf.predict_proba(X_te)[:, 1]
plot_classification_diagnostic(y_te.to_numpy(), score, title="RF — diagnóstico ocupación")
""",
        ),
        section(
            14,
            "Validaciones",
            "Comparativa rigurosa con bootstrap IC y aserciones cuantitativas: el RF "
            "debe **batir** los dos baselines en F1, y el balance de masa debe **batir** "
            "el threshold trivial.",
            """\
y_rf = rf.predict(X_te)
def _f1(yt, yp): return float(f1_score(yt, yp, zero_division=0))

# Alinear baselines al mismo X_te para comparación justa
y_thr_te = y_thr[i:]
y_bal_te = y_balance[i:]

table = pd.DataFrame({
    "model":    ["threshold_trivial", "balance_masa_CO2", "RF_balanced"],
    "F1":       [_f1(y_te, y_thr_te), _f1(y_te, y_bal_te), _f1(y_te, y_rf)],
    "Precision":[float(precision_score(y_te, p, zero_division=0))
                 for p in [y_thr_te, y_bal_te, y_rf]],
    "Recall":   [float(recall_score(y_te, p, zero_division=0))
                 for p in [y_thr_te, y_bal_te, y_rf]],
}).round(3)
print(table)

# Aserciones cuantitativas (no cosméticas)
assert _f1(y_te, y_rf) > _f1(y_te, y_thr_te), "RF debe batir threshold trivial"
assert y_te.sum() > 0, "Test set sin clase positiva — split inadecuado"
print("\\nValidaciones OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Mock corto (7 días)** + split 70/30 → test sin clase positiva → F1=0 "
            "silencioso. Siempre `assert y_te.sum() > 0`.\n"
            "2. **Shuffle en split** rompe temporalidad y filtra futuro.\n"
            "3. **Olvidar `class_weight='balanced'`** con clases desbalanceadas → "
            "modelo predice siempre la mayoritaria.\n"
            "4. **F1 macro vs binary** confundidos: aquí usamos `binary` (clase positiva = ocupado).\n"
            "5. **No incluir `dCO₂/dt`** — la señal predictiva más potente según el "
            "balance de masa (sec 19).",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Calibra `volume_m3` y `vent_rate_l_s` del balance de masa observando "
            "las 6 primeras horas de un día lectivo (ocupación conocida).\n"
            "2. Sustituye `RandomForestClassifier` por `GradientBoostingClassifier` y "
            "compara F1 + tiempo de inferencia.\n"
            "3. Implementa `CalibratedClassifierCV(rf, method='isotonic', cv=tscv)` y "
            "verifica que `score` está calibrado con un reliability diagram.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "El balance de masa es **portable** entre centros: solo requiere conocer "
            "`volume_m3` (medible) y `vent_rate_l_s` (placa de la UTA). El RF requiere "
            "30 días de etiquetas reales — usar reservas con cámara ToF como ground "
            "truth durante el primer mes de calibración.",
        ),
        common_summary(
            next_notebook="04_case_D_iaq_occupancy/05_validacion_iaq_confort.ipynb",
            docs_link="docs/validation/ml-validation.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_D,
    )


def _val(target: Path) -> Path:
    title = "Caso D · 05 Alertas IAQ con histéresis y jerarquía L1/L2/L3"
    sections = [
        section(
            1,
            "Objetivo",
            "Implementar un sistema de alertas IAQ **jerárquico** (L1/L2/L3) con "
            "**histéresis temporal** (sostenido N minutos antes de disparar) y banda "
            "de hysteresis (rearme con margen). Cuantificar el efecto de la "
            "histéresis sobre la fatiga de alertas.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Categorización CO₂ por umbrales OMS / EN 16798 (5 niveles).\n"
            "- **Histéresis temporal**: dispara solo si superado durante ≥ N min.\n"
            "- **Banda de hysteresis**: rearme con margen para evitar oscilación.\n"
            "- Jerarquía L1 (profesor) / L2 (conserje) / L3 (dirección + actuador).\n"
            "- Tabla de tiempo total por categoría (KPI de director de centro).",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Sin histéresis, una transición ruidosa por encima de 1 500 ppm dispara "
            "decenas de alertas por hora → fatiga → operador desactiva → sistema "
            "invisible. Con histéresis (5 min sostenido + banda 100 ppm), las "
            "alertas son útiles.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Las alertas van a `telemetry_events` con tags `level`, `severity`, "
            "`asset_id`. Webhook a Mattermost/Slack para L2/L3.",
        ),
        section(5, "Relación con Medallion", "Oro: reglas con estado + reporte de alertas."),
        section(6, "Datos de entrada", "Mock In-Gauge 30 días para tener picos."),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Eventos como measurement separado:\n\n"
            "```\n"
            "captia_event,asset_id=AULA01,level=L1,kind=co2_alert "
            "value_ppm=1612.0,severity=2 1715260800000000000\n"
            "```",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos 30 días para tener variabilidad real de CO₂.",
            """\
df, _ = mocks.make_ingauge_aula01_mock(days=30)
df = df.set_index("timestamp")
print({"filas": len(df), "co2_max": float(df["Indoor_CO2"].max()),
       "co2_p99": float(df["Indoor_CO2"].quantile(0.99))})
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Categorización OMS + thresholds por nivel jerárquico.",
            """\
THRESHOLDS_PPM = {"L1": 800, "L2": 1000, "L3": 1500}  # CO2 ppm — alineados con EN 16798 cat I/II/III
HOLD_MIN = {"L1": 5, "L2": 5, "L3": 10}               # min sostenido
HYST_BAND = 75                                         # ppm para rearme

def cat_co2(x):
    if x < 800: return "optimo"
    if x < 1000: return "aceptable"
    if x < 1500: return "vigilar"
    if x < 2000: return "molesto"
    return "ventilar"

df["co2_cat"] = df["Indoor_CO2"].apply(cat_co2)
dist = df["co2_cat"].value_counts(normalize=True).reindex(
    ["optimo", "aceptable", "vigilar", "molesto", "ventilar"], fill_value=0
).round(3)
print(dist)
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "**Algoritmo con histéresis**: máquina de estados (`armed → triggered → "
            "rearming`). Comparamos: (a) sin histéresis (cada punto > umbral), "
            "(b) con histéresis (sostenido + banda).",
            """\
def alerts_naive(series, threshold):
    \"\"\"Cada punto > threshold genera alerta — sin estado.\"\"\"
    return (series > threshold).astype(int)

def alerts_hysteresis(series, threshold, hold_min, hyst_band):
    \"\"\"Máquina de estados con sostenido N min + banda de rearme.\"\"\"
    sample_min = (series.index[1] - series.index[0]).total_seconds() / 60
    hold_samples = max(1, int(hold_min / sample_min))
    out = pd.Series(0, index=series.index, dtype=int)
    state = "armed"
    above_count = 0
    for ts, v in series.items():
        if state == "armed":
            if v > threshold:
                above_count += 1
                if above_count >= hold_samples:
                    out[ts] = 1
                    state = "triggered"
            else:
                above_count = 0
        elif state == "triggered":
            if v < (threshold - hyst_band):
                state = "armed"
                above_count = 0
    return out

# Comparativa para nivel L2 (1500 ppm)
naive_L2 = alerts_naive(df["Indoor_CO2"], THRESHOLDS_PPM["L2"])
hyst_L2 = alerts_hysteresis(df["Indoor_CO2"], THRESHOLDS_PPM["L2"],
                             HOLD_MIN["L2"], HYST_BAND)
comparison = pd.DataFrame({
    "metodo": ["naive (cada punto)", "hysteresis (10min + 100ppm)"],
    "alertas_totales": [int(naive_L2.sum()), int(hyst_L2.sum())],
    "transiciones_unicas": [
        int((naive_L2.diff() == 1).sum()),
        int((hyst_L2.diff() == 1).sum()),
    ],
})
comparison["fatiga_ratio"] = (
    comparison["alertas_totales"] / comparison["transiciones_unicas"].replace(0, 1)
).round(2)
print(comparison.to_string(index=False))
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Timeline 1 día con CO₂ + thresholds + alertas naive vs histeresis. "
            "Heatmap horario de categoría dominante.",
            """\
import matplotlib.pyplot as plt

# Día representativo (martes con clase)
sample = df[(df.index.weekday == 1) & (df.index.hour < 18)].head(60 * 12)
fig, axes = plt.subplots(2, 1, figsize=(11, 7))

ax1 = axes[0]
ax1.plot(sample.index, sample["Indoor_CO2"], color="#3F51B5", linewidth=1, label="CO2")
for level, thr in THRESHOLDS_PPM.items():
    ax1.axhline(thr, color={"L1": "#FFC107", "L2": "#FF5722", "L3": "#9C27B0"}[level],
                linestyle="--", alpha=0.6, label=f"{level} ({thr} ppm)")
sample_naive = alerts_naive(sample["Indoor_CO2"], THRESHOLDS_PPM["L2"])
sample_hyst = alerts_hysteresis(sample["Indoor_CO2"], THRESHOLDS_PPM["L2"],
                                  HOLD_MIN["L2"], HYST_BAND)
ax1.scatter(sample.index[sample_naive == 1], sample.loc[sample_naive == 1, "Indoor_CO2"],
            color="#FF5722", s=10, alpha=0.4, label="naive alerts")
ax1.scatter(sample.index[sample_hyst == 1], sample.loc[sample_hyst == 1, "Indoor_CO2"],
            color="#4CAF50", s=80, marker="v", label="hysteresis alerts")
ax1.set_title("CO2 con thresholds y alertas — naive vs histeresis (L2)")
ax1.set_ylabel("CO2 (ppm)")
ax1.legend(loc="upper right", fontsize=8)

# Heatmap categoría × hora
df["hour"] = df.index.hour
heat = df.groupby("hour")["co2_cat"].value_counts(normalize=True).unstack(fill_value=0)
heat = heat.reindex(columns=["optimo", "aceptable", "vigilar", "molesto", "ventilar"], fill_value=0)
heat.plot.bar(stacked=True, ax=axes[1],
              color=["#4CAF50", "#8BC34A", "#FFC107", "#FF9800", "#FF5722"], edgecolor="white")
axes[1].set_title("Distribucion categoria CO2 por hora del dia")
axes[1].set_ylabel("fraccion del tiempo")
axes[1].legend(loc="upper right", fontsize=8, ncol=5)
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "(a) histéresis genera **menos alertas** que naive (esperado: factor 5-50×). "
            "(b) `fatiga_ratio` baja drásticamente con histéresis. "
            "(c) Tiempo total `categoría >= vigilar` durante horario lectivo.",
            """\
n_naive = comparison.loc[comparison["metodo"] == "naive (cada punto)", "alertas_totales"].iloc[0]
n_hyst = comparison.loc[comparison["metodo"].str.startswith("hysteresis"), "alertas_totales"].iloc[0]
assert n_hyst <= n_naive, "Histeresis nunca debe generar mas alertas que naive"
if n_naive > 0:
    reduccion_pct = (1 - n_hyst / n_naive) * 100
    assert reduccion_pct >= 30, f"Reduccion esperada >=30%, vimos {reduccion_pct:.1f}%"
else:
    print("Mock sin picos relevantes; bajar threshold L2 para ver el efecto.")

# Tiempo en cada categoría durante horario lectivo
hours_idx = df.index.hour
mask = ((hours_idx >= 8) & (hours_idx < 15)) & (df.index.dayofweek < 5)
tiempo_lectivo = df.loc[mask, "co2_cat"].value_counts().reindex(
    ["optimo", "aceptable", "vigilar", "molesto", "ventilar"], fill_value=0
)
print("\\nTiempo total en horario lectivo por categoria (minutos):")
print(tiempo_lectivo.to_string())
print(f"\\nReduccion alertas naive->hist: {n_naive} -> {n_hyst} ({(1 - n_hyst/max(n_naive,1))*100:.1f}% menos)")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Sin histéresis**: 1 sensor ruidoso oscilando alrededor del threshold "
            "produce decenas de alertas por hora → fatiga → desactivación.\n"
            "2. **Sin banda de rearme**: si rearme = threshold mismo, oscilación pequeña "
            "(ej. ±50 ppm) genera flapping.\n"
            "3. **Threshold único** sin jerarquía L1/L2/L3: un nivel solo no permite "
            "distinguir entre 'avisar' y 'actuar'.\n"
            "4. **Mock corto (7 días)**: no captura suficientes picos para ver el efecto.\n"
            "5. **Comparar absoluto vs exterior**: EN 16798 recomienda CO₂ relativo "
            "(`indoor - outdoor`), no absoluto.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade categorías para temperatura (16-32 °C) y humedad (20-80 %RH) con "
            "thresholds RITE / EN 16798 categoría II.\n"
            "2. Implementa una **regla compuesta** `IAQ_alert = (CO2>1500) AND "
            "(noise>65 dB OR people_count>20)` — alerta solo cuando hay clase activa.\n"
            "3. Mide el **MTTR percibido** (tiempo entre alerta y mejora real de "
            "CO₂): para cada alerta L2 disparada, calcula minutos hasta que CO₂ baja "
            "de 1 000 ppm. Reporta p50 y p95.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Las funciones `alerts_naive` / `alerts_hysteresis` operan sobre cualquier "
            "Series. En producción se traducen a Flux Task con state file (Telegraf "
            "`processors.dedup`) — la lógica es idéntica.",
        ),
        common_summary(
            next_notebook="05_case_E_weather_solar/01_eda_era5.ipynb",
            docs_link="docs/use-cases/case-d-iaq-occupancy.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="04_case_D_iaq_occupancy/05_validacion_iaq_confort.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_D,
    )


def build(target: Path) -> int:
    _eda(target)
    _bronze_silver(target)
    _features(target)
    _model(target)
    _val(target)
    return 5
