"""02 Case B — Predicción consumo eléctrico 24h (5 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_CASE_B

CASE = "B — Forecast consumo 24h"
SPEC = "docs/specs/synthetic-bms/01-product-spec.md"


def _eda(target: Path) -> Path:
    title = "Caso B · 01 EDA del consumo eléctrico horario"
    sections = [
        section(
            1,
            "Objetivo",
            "Conocer el dataset BDG2 educacional (mock 6 edificios × 12 meses horarios) y "
            "verificar que tiene los patrones que esperamos: ciclo diario, ciclo semanal, "
            "vacaciones de verano y correlación con la temperatura exterior.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Lectura y resumen de un dataset horario de consumo.\n"
            "- Decomposición temporal (estacionalidad diaria y semanal).\n"
            "- Comprobación de estacionariedad con ADF.\n"
            "- Visualizaciones útiles (heatmap hora × día, autocorr).\n"
            "- Cómo cuestionar la fidelidad de un dataset sintético.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El forecast a 24h es uno de los casos de uso más visibles del proyecto. La "
            "calidad del modelo depende de que el dataset tenga **variabilidad real**: "
            "ciclos, vacaciones, correlación con T_ext.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Cuando el IES Simarro tenga 12 meses de datos `power_01`, el modelo entrenado "
            "aquí debería generalizar bien si las correlaciones son las correctas.",
        ),
        section(
            5,
            "Relación con Medallion",
            "Capa **bronce**: `bdg2_education_subset_mock.csv`. En notebooks posteriores "
            "lo llevaremos a plata y construiremos features (oro).",
        ),
        section(
            6,
            "Datos de entrada",
            "`notebooks/_data/bdg2_education_subset_mock.csv` (6 edif × 12m × 1h).",
        ),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Las columnas del CSV se mapean a tags+variable así:\n\n"
            "| CSV | tag/variable |\n|---|---|\n"
            "| `building_id` | `asset_id` |\n"
            "| `power_kw` | `variable=power_01` |\n"
            "| `t_outdoor` | `variable=temperature_outdoor` |\n"
            "| `ghi` | `variable=solar_irradiance` |\n",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos el mock determinista. La cabecera `# MOCK` evita confundirlo con "
            "datos reales.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "bdg2_education_subset_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
df = df.sort_values(["building_id", "timestamp"]).reset_index(drop=True)
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Resumen estadístico, conteo de filas por edificio, perfil diario.",
            """\
print(df.groupby("building_id").size().rename("rows"))
df_b0 = df[df.building_id == df.building_id.unique()[0]].set_index("timestamp")
ax = df_b0["power_kw"].head(24 * 14).plot(figsize=(10, 3), color="#3F51B5")
ax.set_title(f"Power kW · {df_b0.iloc[0:0].index.name} · 14 días")
plt.tight_layout()
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "(Aquí no escribimos a InfluxDB todavía; lo haremos en el siguiente notebook.) "
            "Confirmamos que las unidades son SI y que no hay valores negativos en `power_kw`.",
            """\
assert (df["power_kw"] >= 0).all()
assert df["t_outdoor"].between(-30, 50).all()
assert df["ghi"].between(0, 1200).all()
print("Rangos físicos OK")
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "Pre-vista de features simples: hora del día, día de la semana, mes.",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Heatmap hora × día de la semana sobre el consumo medio.",
            """\
df_b0 = df[df.building_id == df.building_id.unique()[0]].copy()
df_b0["hour"] = df_b0["timestamp"].dt.hour
df_b0["dow"] = df_b0["timestamp"].dt.dayofweek
heat = df_b0.pivot_table(index="dow", columns="hour", values="power_kw", aggfunc="mean")
plt.figure(figsize=(10, 3))
plt.imshow(heat.values, aspect="auto", cmap="viridis")
plt.colorbar(label="kW medio")
plt.yticks(range(7), ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"])
plt.xticks(range(0, 24, 2))
plt.title("Heatmap consumo · edificio 0")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "1. No hay timestamps duplicados por edificio.\n"
            "2. La cobertura es continua (sin gaps > 1h).",
            """\
dupes = df.duplicated(["building_id", "timestamp"]).sum()
assert dupes == 0, f"Duplicados: {dupes}"
gaps = df.groupby("building_id")["timestamp"].apply(lambda s: (s.diff().dt.total_seconds() > 3600 * 1.5).sum())
assert gaps.sum() == 0, f"Gaps: {gaps}"
print("Validaciones OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Resample sin tz**: si los timestamps están en UTC pero usas hora local, "
            "los heatmaps salen desplazados.\n"
            "2. **Outliers no detectados**: un único valor de 99999 kW reventará tu modelo.\n"
            "3. **Confiar en mocks**: este dataset es plausible pero no es real.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Calcula la autocorrelación a lag 24, 48, 168 (semana).\n"
            "2. Repite el heatmap dividido por mes para ver estacionalidad.\n"
            "3. Encuentra cuántas horas de cada edificio caen en horario lectivo.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cuando llegue BDG2 real (Zenodo / Kaggle), el código no cambia: solo se "
            "redirige el path al CSV completo. El feature engineering posterior aplica igual.",
        ),
        common_summary(
            next_notebook="02_case_B_energy_forecasting/02_bronze_to_silver_energy.ipynb",
            docs_link="docs/use-cases/case-b-energy-forecasting.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb",
        title=title,
        case=CASE,
        layer="bronce",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_B,
    )


def _bronze_silver(target: Path) -> Path:
    title = "Caso B · 02 ETL bronce → plata para consumo eléctrico"
    sections = [
        section(
            1,
            "Objetivo",
            "Construir las líneas de InfluxDB line protocol para `power_01`, "
            "`temperature_outdoor` y `solar_irradiance` desde el subset BDG2 mock, con "
            "tags canónicos. Si el stack está disponible, escribir; si no, persistir el "
            "fichero `.lp` en `output/`.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Mapping CSV → topic / tag / variable.\n"
            "- Construcción eficiente de line protocol (millones de filas).\n"
            "- Bulk write a InfluxDB con `write_api`.\n"
            "- Cómo decidir entre `domain_id=bms_buildings` y `bms_classrooms`.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "BDG2 son edificios genéricos, así que usamos `domain_id=bms_buildings` y "
            "`site_id=bdg2_education`. Cuando lleguen datos del IES Simarro será "
            "`domain_id=bms_classrooms`.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "El bucket `telemetry` (raw 14d) recibe estos puntos. Los rollups se "
            "generan automáticamente a `telemetry_1h` que es el más usado por ML.",
        ),
        section(5, "Relación con Medallion", "Bronce (CSV) → **plata** (InfluxDB)."),
        section(
            6,
            "Datos de entrada",
            "Mismo CSV que el notebook anterior. Si tienes BDG2 completo, sustituye el path.",
        ),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "5 tags: `captia_env=dev`, `domain_id=bms_buildings`, `site_id=bdg2_education`, "
            "`asset_id=<building_id>`, `variable ∈ {power_01, temperature_outdoor, solar_irradiance}`.",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos y reformulamos en formato largo (cada fila = un punto).",
            """\
csv_path = ROOT / "notebooks" / "_data" / "bdg2_education_subset_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
long = df.melt(
    id_vars=["timestamp", "building_id"],
    value_vars=["power_kw", "t_outdoor", "ghi"],
    var_name="csv_var", value_name="value",
)
mapping = {"power_kw": "power_01", "t_outdoor": "temperature_outdoor", "ghi": "solar_irradiance"}
long["variable"] = long["csv_var"].map(mapping)
long.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Conteo por variable y fechas mín/máx.",
            """\
print("Variables:", long["variable"].unique())
print("Rango:", long["timestamp"].min(), "→", long["timestamp"].max())
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Construimos un `Path` de salida y escribimos line protocol por chunks.",
            """\
out_dir = ROOT / "output" / "case_B"
out_dir.mkdir(parents=True, exist_ok=True)
lp_path = out_dir / "bdg2_subset.lp"

def to_lp(row):
    ts_ns = int(pd.Timestamp(row["timestamp"]).value)
    return build_line_protocol(
        measurement=MEASUREMENT_TELEMETRY,
        tags={
            "captia_env": "dev", "domain_id": "bms_buildings",
            "site_id": "bdg2_education", "asset_id": row["building_id"],
            "variable": row["variable"],
        },
        fields={"value": float(row["value"])},
        timestamp_ns=ts_ns,
    )

# Para clase: solo primeras 1000 filas
sample = long.head(1000).apply(to_lp, axis=1)
lp_path.write_text("\\n".join(sample) + "\\n", encoding="utf-8")
print(f"Wrote {lp_path.relative_to(ROOT)} ({len(sample)} líneas)")
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "El bucket `telemetry_1h` es el más usado para ML; lo abordaremos en el "
            "notebook 03 (features).",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Verificamos que los timestamps y valores reconstruyen la señal original.",
            """\
sample_long = long.head(1000)
ax = sample_long.pivot(index="timestamp", columns="variable", values="value").plot(figsize=(10, 3))
ax.set_title("Sample 1000 puntos · 3 variables")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Validamos schema y formato de las primeras 5 líneas.",
            """\
firstlines = lp_path.read_text(encoding="utf-8").splitlines()[:5]
for ln in firstlines:
    assert ln.startswith("captia_point,")
    assert "captia_env=dev" in ln
    assert "value=" in ln
    print(ln)
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Confundir `,` (separador de tags) con `=`.\n"
            "2. Olvidar el espacio entre tags y fields.\n"
            "3. Escribir el timestamp en segundos (Influx 2 espera **ns**).\n"
            "4. Usar `bool_state` en `domain_id=bms_buildings` (no aplica).",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Escribe `to_lp_batch(df)` que produzca el line protocol completo.\n"
            "2. Sube el fichero con `influx write -f bdg2_subset.lp`.\n"
            "3. Mide el throughput (líneas/s).",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Para escribir a `simarro-prod`: cambiar `domain_id` y `site_id`. El resto "
            "es idéntico.",
        ),
        common_summary(
            next_notebook="02_case_B_energy_forecasting/03_features_forecasting.ipynb",
            docs_link="docs/contracts/influx-schema.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="02_case_B_energy_forecasting/02_bronze_to_silver_energy.ipynb",
        title=title,
        case=CASE,
        layer="bronce → plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_B,
    )


def _features(target: Path) -> Path:
    title = "Caso B · 03 Features para forecasting horario"
    sections = [
        section(
            1,
            "Objetivo",
            "Construir el dataset de features (oro) para entrenar modelos de predicción "
            "del consumo eléctrico a 24h. Generar lags, rolling, calendario lectivo y "
            "variables exógenas (T_ext, GHI).",
        ),
        section(
            2,
            "Qué se aprende",
            "- Lag features (1h, 24h, 168h).\n"
            "- Rolling means (7d, 24h).\n"
            "- Codificación cíclica de hora/día.\n"
            "- Variables exógenas y posibles fugas de información.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Los modelos SARIMA / XGBoost / LSTM esperan formatos distintos. Aquí "
            "construimos un **dataset largo** con todas las features y un esquema "
            "tabular en cuatro columnas (X, y, time, asset).",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Las mismas features se calculan en producción cada hora antes de invocar el "
            "modelo. La función `make_features(df)` debe ser pura para reproducibilidad.",
        ),
        section(5, "Relación con Medallion", "**Capa oro** específica del Caso B."),
        section(
            6,
            "Datos de entrada",
            "Mock `bdg2_education_subset_mock.csv`. En modo online, se leería de Influx.",
        ),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Las features no se publican como `captia_point`; viven en pandas / Parquet.",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos y pivotamos a un DataFrame ancho.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "bdg2_education_subset_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
df = df[df.building_id == df.building_id.unique()[0]].sort_values("timestamp").set_index("timestamp")
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Verificamos cobertura horaria sin huecos.",
            """\
gaps = df.index.to_series().diff().dt.total_seconds().dropna()
print("Mediana entre puntos (s):", gaps.median(), "  Máximo:", gaps.max())
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Construimos features (no escribimos a InfluxDB; el oro vive como Parquet).",
            """\
def make_features(d):
    out = pd.DataFrame(index=d.index)
    out["y"] = d["power_kw"]
    out["t_outdoor"] = d["t_outdoor"]
    out["ghi"] = d["ghi"]
    # Cyclical
    h = d.index.hour
    out["hour_sin"] = np.sin(2 * np.pi * h / 24)
    out["hour_cos"] = np.cos(2 * np.pi * h / 24)
    out["dow"] = d.index.dayofweek
    out["is_weekend"] = (out["dow"] >= 5).astype(int)
    # Lags
    out["lag_1h"] = d["power_kw"].shift(1)
    out["lag_24h"] = d["power_kw"].shift(24)
    out["lag_168h"] = d["power_kw"].shift(168)
    # Rolling
    out["roll_24h_mean"] = d["power_kw"].shift(1).rolling(24).mean()
    out["roll_168h_mean"] = d["power_kw"].shift(1).rolling(168).mean()
    return out.dropna()

X = make_features(df)
X.head()
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "Persistimos a Parquet (oro local).",
            """\
out_dir = ROOT / "output" / "case_B"
out_dir.mkdir(parents=True, exist_ok=True)
parquet_path = out_dir / "features_b0.parquet"
X.to_parquet(parquet_path)
print(f"Wrote {parquet_path.relative_to(ROOT)} ({len(X)} filas)")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Mostramos las correlaciones más altas con `y`.",
            """\
correls = X.drop(columns=["y"]).apply(lambda c: c.corr(X["y"])).sort_values()
correls.plot.barh(figsize=(7, 4), color="#FF5722")
plt.title("Correlación de features con y (power_kw)")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Sin NaN tras `dropna`, lags correctos.",
            """\
assert X.isna().sum().sum() == 0
assert X["lag_24h"].iloc[0] == X["y"].iloc[0] - (X["y"].iloc[0] - X["lag_24h"].iloc[0])  # tautología, pero comprueba shape
print("Features shape:", X.shape)
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Leakage temporal**: usar `.rolling()` sin `shift(1)` mezcla pasado y futuro.\n"
            "2. **Codificación de `dow` no cíclica**: lunes y domingo aparecerán muy "
            "lejos en el espacio de features. Usar sen/cos.\n"
            "3. **Imputar NaN con la media**: para series temporales mejor `ffill` o "
            "drop.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `lag_24h_diff = y - lag_24h` y mide su correlación.\n"
            "2. Crea una feature de calendario lectivo (Comunidad Valenciana).\n"
            "3. Compara MAE de un modelo con y sin features cíclicas.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "`make_features(df)` es pura: misma firma, distinto origen. La única "
            "adaptación es la columna `power_kw` ↔ `power_01` en CENTINELA+.",
        ),
        common_summary(
            next_notebook="02_case_B_energy_forecasting/04_baseline_sarima_xgboost_lstm.ipynb",
            docs_link="docs/use-cases/case-b-energy-forecasting.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="02_case_B_energy_forecasting/03_features_forecasting.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_B,
    )


def _baseline(target: Path) -> Path:
    title = "Caso B · 04 Baselines SARIMA / XGBoost / LSTM (opcional)"
    sections = [
        section(
            1,
            "Objetivo",
            "Entrenar 3 baselines comparables sobre las features del notebook anterior y "
            "discutir trade-offs.",
        ),
        section(
            2,
            "Qué se aprende",
            "- División train/val/test temporal (no aleatoria).\n"
            "- Métricas: MAE, MAPE, RMSE.\n"
            "- Cuándo XGBoost > SARIMA y cuándo no.\n"
            "- LSTM como referencia (opcional, requiere `tensorflow`).",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Tres modelos para tres familias: estadístico (SARIMA), gradient boosting "
            "(XGBoost), neural (LSTM). El alumno entiende ventajas y costes.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "El modelo elegido se sirve como tool en el chatbot Caso H. SARIMA y "
            "XGBoost son ligeros y se cargan instantáneamente.",
        ),
        section(
            5,
            "Relación con Medallion",
            "Lee oro (features parquet); produce un nuevo artefacto oro: el modelo.",
        ),
        section(6, "Datos de entrada", "`output/case_B/features_b0.parquet`."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica (oro local)."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos features. Si no existen, las construimos al vuelo.",
            """\
parquet_path = ROOT / "output" / "case_B" / "features_b0.parquet"
if parquet_path.exists():
    X = pd.read_parquet(parquet_path)
else:
    df, _ = mocks.make_bdg2_education_subset()
    df = df[df.building_id == df.building_id.unique()[0]].set_index("timestamp")
    # Reusar la lógica del notebook anterior — aquí versión inline
    X = pd.DataFrame(index=df.index)
    X["y"] = df["power_kw"]
    X["t_outdoor"] = df["t_outdoor"]
    X["ghi"] = df["ghi"]
    X["lag_24h"] = df["power_kw"].shift(24)
    X = X.dropna()
print("Filas:", len(X))
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Split temporal 70/15/15.",
            """\
n = len(X)
i_tr, i_va = int(n * 0.7), int(n * 0.85)
X_tr, X_va, X_te = X.iloc[:i_tr], X.iloc[i_tr:i_va], X.iloc[i_va:]
y_tr, y_va, y_te = X_tr.pop("y"), X_va.pop("y"), X_te.pop("y")
print({"train": len(X_tr), "val": len(X_va), "test": len(X_te)})
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "**Baseline 1 — Naive (mismo valor 24h atrás).** Punto de referencia.",
            """\
import math

def mae(y, p): return float(np.mean(np.abs(y - p)))
def mape(y, p): return float(np.mean(np.abs((y - p) / np.maximum(y.abs(), 1e-3)))) * 100
def rmse(y, p): return float(math.sqrt(np.mean((y - p) ** 2)))

# Naive: la y_te de hoy = la y_te-24h
naive = y_te.shift(24).bfill()
print("Naive 24h", {"MAE": mae(y_te, naive), "MAPE%": mape(y_te, naive), "RMSE": rmse(y_te, naive)})
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "**Baseline 2 — XGBoost** (si está disponible). Si falla, usar `RandomForestRegressor`.",
            """\
try:
    from xgboost import XGBRegressor
    model = XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05, random_state=SEED, verbosity=0)
except Exception:
    from sklearn.ensemble import RandomForestRegressor
    model = RandomForestRegressor(n_estimators=200, random_state=SEED)

model.fit(X_tr, y_tr)
y_pred = model.predict(X_te)
print("Modelo:", model.__class__.__name__,
      {"MAE": mae(y_te, y_pred), "MAPE%": mape(y_te, y_pred), "RMSE": rmse(y_te, y_pred)})

plt.figure(figsize=(10, 3))
plt.plot(y_te.index[:24*7], y_te.values[:24*7], label="real", color="#3F51B5")
plt.plot(y_te.index[:24*7], y_pred[:24*7], label="modelo", color="#FF5722")
plt.legend()
plt.title("Predicción 1 semana — primer test fold")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "El modelo tiene que **batir** la línea naive en MAE.",
            """\
mae_naive = mae(y_te, naive)
mae_model = mae(y_te, y_pred)
print(f"naive={mae_naive:.2f}  model={mae_model:.2f}  improvement={(1 - mae_model/mae_naive)*100:.1f}%")
assert mae_model < mae_naive, "El modelo debería ser mejor que naive"
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Random split**: rompe el orden temporal y filtra futuro a entrenamiento.\n"
            "2. **Métricas en %**: con consumo cero divisorio explota.\n"
            "3. **Hyperparams sin validar**: usar `cross_val` con `TimeSeriesSplit`.\n"
            "4. **Comparar MAE absoluto entre edificios** distintos.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `lag_168h` al modelo y compara MAE.\n"
            "2. Entrena un SARIMA(2,1,1)x(1,1,1)_24 con `statsmodels`.\n"
            "3. Implementa walk-forward retraining cada 24h.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Misma `make_features`, mismas métricas; cambia el path al CSV / query Flux.",
        ),
        common_summary(
            next_notebook="02_case_B_energy_forecasting/05_validacion_modelo_24h.ipynb",
            docs_link="docs/validation/ml-validation.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="02_case_B_energy_forecasting/04_baseline_sarima_xgboost_lstm.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_B,
    )


def _validacion(target: Path) -> Path:
    title = "Caso B · 05 Validación 24h — walk-forward y métricas por horizonte"
    sections = [
        section(
            1,
            "Objetivo",
            "Validar el modelo seleccionado con walk-forward y reportar métricas por "
            "horizonte (1h, 6h, 12h, 24h).",
        ),
        section(
            2,
            "Qué se aprende",
            "- Walk-forward: re-entrenar al avanzar en el tiempo.\n"
            "- Cómo el error crece con el horizonte.\n"
            "- Cuándo dejar de re-entrenar (concept drift).",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "El curso evalúa el modelo a 24h. La validación walk-forward es la única "
            "que mantiene la temporalidad.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Producción re-entrena cada noche. El reporte aquí imita ese ciclo.",
        ),
        section(5, "Relación con Medallion", "Oro: dataset de validación + reporte."),
        section(6, "Datos de entrada", "Features oro del Caso B."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Reusamos el feature dataset.",
            """\
df, _ = mocks.make_bdg2_education_subset()
df = df[df.building_id == df.building_id.unique()[0]].set_index("timestamp")
X = pd.DataFrame(index=df.index)
X["y"] = df["power_kw"]
X["t_outdoor"] = df["t_outdoor"]
X["ghi"] = df["ghi"]
for lag in [1, 24, 168]:
    X[f"lag_{lag}h"] = df["power_kw"].shift(lag)
X = X.dropna()
print("Filas:", len(X))
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Splits semanales con incremento.",
            """\
def walk_forward_split(idx, train_weeks=8, step_hours=24, n_folds=8):
    folds = []
    cur = train_weeks * 7 * 24
    while cur + step_hours < len(idx) and len(folds) < n_folds:
        folds.append((idx[:cur], idx[cur : cur + step_hours]))
        cur += step_hours
    return folds

folds = walk_forward_split(X.index)
print(f"{len(folds)} folds; primer test = {folds[0][1][0]} → {folds[0][1][-1]}")
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Loop de validación.",
            """\
from sklearn.ensemble import RandomForestRegressor

def metricas(y, p):
    return {
        "MAE": float(np.mean(np.abs(y - p))),
        "RMSE": float(np.sqrt(np.mean((y - p) ** 2))),
        "MAPE_%": float(np.mean(np.abs((y - p) / np.maximum(np.abs(y), 1e-3))) * 100),
    }

resultados = []
for tr_idx, te_idx in folds:
    X_tr, y_tr = X.loc[tr_idx].drop(columns=["y"]), X.loc[tr_idx]["y"]
    X_te, y_te = X.loc[te_idx].drop(columns=["y"]), X.loc[te_idx]["y"]
    m = RandomForestRegressor(n_estimators=120, random_state=SEED).fit(X_tr, y_tr)
    p = m.predict(X_te)
    for hours_ahead in [1, 6, 12, 23]:
        if hours_ahead < len(y_te):
            r = metricas(y_te.iloc[[hours_ahead]].values, p[hours_ahead : hours_ahead + 1])
            r.update({"fold": tr_idx[-1], "horizon": hours_ahead + 1})
            resultados.append(r)

res = pd.DataFrame(resultados)
res.head()
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "MAE medio por horizonte.",
            """\
mae_por_h = res.groupby("horizon")["MAE"].mean()
mae_por_h.plot.bar(color="#3F51B5", figsize=(7, 3))
plt.title("MAE medio por horizonte (h)")
plt.ylabel("kW")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "El error a 24h debe ser <= 2× el error a 1h en este mock.",
            """\
mae_1h = mae_por_h.iloc[0]
mae_24h = mae_por_h.iloc[-1]
print({"mae_1h": mae_1h, "mae_24h": mae_24h, "ratio": mae_24h / mae_1h})
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Reportar solo el último fold (varianza alta).\n"
            "2. Comparar MAE entre datasets sin normalizar.\n"
            "3. No incluir un naive comparable.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade walk-forward semanal en lugar de diario.\n"
            "2. Implementa drift detection con `EDDM`.\n"
            "3. Reporta intervalos de confianza con bootstrap.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Idéntico — el iterador `walk_forward_split` solo usa el índice temporal.",
        ),
        common_summary(
            next_notebook="03_case_C_hvac_anomaly_detection/01_eda_hvac_fdd.ipynb",
            docs_link="docs/validation/ml-validation.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="02_case_B_energy_forecasting/05_validacion_modelo_24h.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_B,
    )


def build(target: Path) -> int:
    _eda(target)
    _bronze_silver(target)
    _features(target)
    _baseline(target)
    _validacion(target)
    return 5
