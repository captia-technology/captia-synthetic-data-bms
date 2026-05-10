"""04 Case D — Calidad de aire, confort y ocupación (5 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section

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
        section(7, "Schema CAPTIA esperado", "Mapping In-Gauge → CAPTIA visto en docs."),
        setup_section(),
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
        section(
            7,
            "Schema CAPTIA esperado",
            "Two outputs: telemetría `.lp` y metadata `.lp` para `captia_metadata`.",
        ),
        setup_section(),
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
for line in state_lines[:5]:
    m = re.search(r"value=([0-9.]+)", line)
    val = float(m.group(1))
    assert val in {0.0, 1.0}, f"Bad value: {val}"
print("State_events OK · ejemplo:", state_lines[0])
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
        section(7, "Schema CAPTIA esperado", "No aplica (oro)."),
        setup_section(),
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
    )


def _model(target: Path) -> Path:
    title = "Caso D · 04 Modelo de ocupación desde ambiente"
    sections = [
        section(
            1,
            "Objetivo",
            "Entrenar un Random Forest baseline + Logistic regression para clasificar "
            "ocupación. Reportar F1 con cross-validation temporal.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Cross-validation temporal (no shuffle).\n"
            "- Métricas con desbalance.\n"
            "- Feature importance.\n"
            "- Cuándo usar Logistic vs RF.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El modelo se servirá como tool del chatbot del Caso H (`get_building_state`).",
        ),
        section(4, "Relación con CENTINELA+", "Tool en producción."),
        section(5, "Relación con Medallion", "Oro: modelo entrenado."),
        section(6, "Datos de entrada", "Oro features Caso D."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos features.",
            """\
parquet_path = ROOT / "output" / "case_D" / "iaq_features.parquet"
if parquet_path.exists():
    X = pd.read_parquet(parquet_path)
else:
    df, _ = mocks.make_ingauge_aula01_mock()
    X = pd.DataFrame({
        "co2": df["Indoor_CO2"], "noise": df["Indoor_Noise"],
        "lux": df["Indoor_Lux"], "y_occupied": df["Occupied"],
    }, index=df["timestamp"]).dropna()
print(X.shape)
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Train/val temporal.",
            """\
y = X.pop("y_occupied")
n = len(X)
i = int(n * 0.7)
X_tr, X_te = X.iloc[:i], X.iloc[i:]
y_tr, y_te = y.iloc[:i], y.iloc[i:]
print(len(X_tr), len(X_te))
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Modelos.",
            """\
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_recall_fscore_support

rf = RandomForestClassifier(n_estimators=200, random_state=SEED).fit(X_tr, y_tr)
lr = LogisticRegression(max_iter=2000, random_state=SEED).fit(X_tr, y_tr)
y_rf = rf.predict(X_te)
y_lr = lr.predict(X_te)
print({"RF F1": f1_score(y_te, y_rf), "LR F1": f1_score(y_te, y_lr)})
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Feature importance del RF.",
            """\
imp = pd.Series(rf.feature_importances_, index=X.columns).sort_values()
imp.plot.barh(color="#3F51B5", figsize=(7, 3))
plt.title("Feature importance — Random Forest")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "RF F1 > LR F1 (esperable con features no lineales).",
            """\
assert f1_score(y_te, y_rf) >= f1_score(y_te, y_lr) - 0.05
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Shuffle en split (rompe temporalidad).\n"
            "2. F1 macro vs binary.\n"
            "3. Olvidar `class_weight='balanced'` cuando hay desbalance fuerte.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `dco2_5min` y observa la mejora.\n"
            "2. Usa `TimeSeriesSplit` con 5 folds.\n"
            "3. Construye un calibrador `CalibratedClassifierCV`.",
        ),
        section(17, "Cómo se reutiliza con datos reales", "Idéntico — cambia path."),
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
    )


def _val(target: Path) -> Path:
    title = "Caso D · 05 Validación IAQ y alertas según OMS / EN 16798"
    sections = [
        section(
            1,
            "Objetivo",
            "Implementar un agregador IAQ que dispara alertas cuando los valores "
            "salen de los rangos recomendados por OMS / EN 16798.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Mapear rangos a categorías.\n"
            "- Generar alertas por minuto.\n"
            "- Visualizar tiempos en cada categoría.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El profesor recibe alertas cuando CO₂ > 1500 ppm o IAQ > 200 — señal de ventilar.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Las alertas van a `telemetry_events` o se exponen vía API REST.",
        ),
        section(5, "Relación con Medallion", "Oro: regla + reporte."),
        section(6, "Datos de entrada", "Mock In-Gauge."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(
            9,
            "Carga de datos o mock",
            "Reusamos In-Gauge.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "ingauge_aula01_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"]).set_index("timestamp")
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Categorización CO₂.",
            """\
def cat_co2(x):
    if x < 800: return "óptimo"
    if x < 1000: return "aceptable"
    if x < 1500: return "vigilar"
    if x < 2000: return "molesto"
    return "ventilar"

df["co2_cat"] = df["Indoor_CO2"].apply(cat_co2)
print(df["co2_cat"].value_counts(normalize=True).round(3))
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Generamos alertas.",
            """\
alertas = df[df["Indoor_CO2"] > 1500].copy()
alertas["msg"] = alertas["Indoor_CO2"].apply(lambda v: f"CO2={int(v)} ppm — abrir ventanas")
print(alertas[["msg"]].head())
print(f"Total alertas: {len(alertas)}")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Heatmap horario de la categoría más frecuente.",
            """\
df["hour"] = df.index.hour
heat = (df.groupby("hour")["co2_cat"]
          .value_counts(normalize=True)
          .unstack(fill_value=0))
heat.plot.bar(stacked=True, figsize=(10, 3), colormap="viridis")
plt.title("Categoría CO2 por hora")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Confirmamos que ningún valor en horario lectivo cae en `extremo` con el "
            "mock (debería ser raro).",
            """\
mask = (df.index.hour.isin(range(8, 15))) & (df.index.dayofweek < 5)
extremo = (df.loc[mask, "Indoor_CO2"] > 4000).sum()
print(f"Extremo en lectivo: {extremo} puntos")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Threshold único**: usar tabla con varias categorías.\n"
            "2. **Olvidar histeresis**: alertas oscilantes.\n"
            "3. **Comparar contra exterior**: la regla EN 16798 lo recomienda.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade categorías para temperatura.\n"
            "2. Implementa histeresis (alerta solo si > 1500 durante > 5 min).\n"
            "3. Crea una regla compuesta CO₂ + ruido.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Mismas reglas se aplican vía Flux task; ya tenemos un esqueleto.",
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
    )


def build(target: Path) -> int:
    _eda(target)
    _bronze_silver(target)
    _features(target)
    _model(target)
    _val(target)
    return 5
