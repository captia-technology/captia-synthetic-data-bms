"""05 Case E — Meteorología y predicción de generación solar (4 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_CASE_E

CASE = "E — Meteo & solar"
SPEC = "docs/specs/synthetic-bms/02-domain-spec.md"


def _eda(target: Path) -> Path:
    title = "Caso E · 01 EDA ERA5 Xàtiva (mock)"
    sections = [
        section(
            1,
            "Objetivo",
            "Conocer la estructura de ERA5 (mock 30 días Xàtiva) y derivar variables útiles "
            "para Caso B (forecast eléctrico) y Caso H (chatbot meteorológico).",
        ),
        section(
            2,
            "Qué se aprende",
            "- Variables ERA5 horarias: T_air, GHI, viento, lluvia, presión.\n"
            "- Cómo descargar ERA5 real (CDS API) — fuera del repo.\n"
            "- Conversiones unitarias: K→°C, J/m²→W/m², m→mm.\n"
            "- Estacionalidad y diurnal cycle.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "ERA5 es el reanálisis climático global del ECMWF. Para Xàtiva tenemos un "
            "mock con 30 días horarios; el dataset real cubre desde 1940.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "El dominio `weather_station/xativa/era5_gridpoint` complementa los "
            "edificios con variables externas correlacionadas.",
        ),
        section(
            5,
            "Relación con Medallion",
            "Bronce: NetCDF / mock CSV. Plata: `captia_point` con domain `weather_station`.",
        ),
        section(6, "Datos de entrada", "`era5_xativa_mock.csv`."),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Tags: `captia_env=dev`, `domain_id=weather_station`, `site_id=xativa`, "
            "`asset_id=era5_gridpoint`, `variable ∈ {temperature_outdoor, solar_irradiance, ...}`.",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos mock.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "era5_xativa_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Estadísticas básicas y diurnal cycle.",
            """\
print(df.describe().round(2))
df["hour"] = df["timestamp"].dt.hour
df.groupby("hour")[["t_air_c", "ghi_w_m2"]].mean().round(2)
""",
        ),
        section(11, "Transformación bronce → plata", "Notebook siguiente."),
        section(12, "Construcción de capa oro", "Notebook 03+04."),
        section(
            13,
            "Visualizaciones explicativas",
            "T y GHI horarios.",
            """\
fig, ax1 = plt.subplots(figsize=(10, 3))
ax1.plot(df["timestamp"], df["t_air_c"], color="#FF5722", label="T")
ax1.set_ylabel("°C")
ax2 = ax1.twinx()
ax2.plot(df["timestamp"], df["ghi_w_m2"], color="#FFC107", label="GHI")
ax2.set_ylabel("W/m²")
plt.title("Diurnal — Xàtiva mock 30 días")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "GHI nunca > 1100 W/m²; T entre -5 y 45.",
            """\
assert df["ghi_w_m2"].between(0, 1100).all()
assert df["t_air_c"].between(-5, 50).all()
print("Rangos OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Confundir GHI con DNI (Direct Normal Irradiance).\n"
            "2. Asumir que `pressure_hpa` es a nivel del mar (es local).\n"
            "3. Promediar viento sin orientación (vector vs escalar).",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Calcula la insolación diaria (kWh/m²/día).\n"
            "2. Compara `t_air_c` con la curva esperada para Csa.\n"
            "3. Dibuja la rosa de los vientos.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Para descargar ERA5 real: registrarse en CDS, instalar `cdsapi`, "
            "ejecutar el script `scripts/era5_download.py` (no incluido).",
        ),
        common_summary(
            next_notebook="05_case_E_weather_solar/02_bronze_to_silver_weather.ipynb",
            docs_link="docs/use-cases/case-e-weather-solar.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="05_case_E_weather_solar/01_eda_era5.ipynb",
        title=title,
        case=CASE,
        layer="bronce",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_E,
    )


def _bronze_silver(target: Path) -> Path:
    title = "Caso E · 02 ETL ERA5 → CAPTIA weather_station"
    sections = [
        section(
            1,
            "Objetivo",
            "Convertir el mock ERA5 a `captia_point` con `domain_id=weather_station`. "
            "Aplicar conversiones unitarias y validar rangos físicos.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Conversión K→°C, J/m²→W/m², m→mm.\n"
            "- Cómo asignar `asset_id=era5_gridpoint`.\n"
            "- Validaciones físicas previas a la escritura.",
        ),
        section(3, "Contexto del caso de uso", "Los datos meteo se usan en B y H."),
        section(4, "Relación con CENTINELA+", "Site `xativa` independiente del aula."),
        section(5, "Relación con Medallion", "Bronce → plata."),
        section(6, "Datos de entrada", "`era5_xativa_mock.csv`."),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "5 variables: `temperature_outdoor`, `solar_irradiance`, `wind_speed`, "
            "`precipitation`, `pressure`.",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "era5_xativa_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Mapping unidades.",
            """\
mapping = {
    "t_air_c": "temperature_outdoor",
    "ghi_w_m2": "solar_irradiance",
    "wind_speed_ms": "wind_speed",
    "precip_mm": "precipitation",
    "pressure_hpa": "pressure",
}
print(mapping)
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Generamos line protocol.",
            """\
out_dir = ROOT / "output" / "case_E"
out_dir.mkdir(parents=True, exist_ok=True)
lines = []
for _, row in df.iterrows():
    ts_ns = int(pd.Timestamp(row["timestamp"]).value)
    for csv_col, captia_var in mapping.items():
        lines.append(build_line_protocol(
            measurement=MEASUREMENT_TELEMETRY,
            tags={
                "captia_env": "dev", "domain_id": "weather_station",
                "site_id": "xativa", "asset_id": "era5_gridpoint",
                "variable": captia_var,
            },
            fields={"value": float(row[csv_col])},
            timestamp_ns=ts_ns,
        ))
(out_dir / "era5_xativa.lp").write_text("\\n".join(lines), encoding="utf-8")
print(f"{len(lines)} líneas escritas")
""",
        ),
        section(12, "Construcción de capa oro", "Notebook 04."),
        section(
            13,
            "Visualizaciones explicativas",
            "Resumen anual sintético.",
            """\
df.set_index("timestamp")[["t_air_c", "ghi_w_m2"]].plot(figsize=(10, 3))
plt.title("ERA5 Xàtiva mock 30 días")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Los rangos físicos se respetan en `captia_point_meta`.",
            """\
for csv_col, var in mapping.items():
    rmin, rmax = KNOWN_VARIABLES[var]["range"]
    s = df[csv_col]
    assert s.between(rmin - 5, rmax + 5).all(), f"{var} fuera de rango"
print("Rangos físicos OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Confundir `solar_irradiance` (GHI) con `solar_irradiance_dni`.\n"
            "2. No restar 273.15 si trabajas con K.\n"
            "3. Confundir tasa (J/s/m²) con energía acumulada (J/m²).",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `dewpoint` calculada con la fórmula de Magnus.\n"
            "2. Mapea `total_cloud_cover` (NetCDF real).\n"
            "3. Construye un downsample diario.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cambiar el path al NetCDF real y `xarray.open_dataset` en vez de `pd.read_csv`.",
        ),
        common_summary(
            next_notebook="05_case_E_weather_solar/03_features_meteorologicas.ipynb",
            docs_link="docs/contracts/variable-catalog.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="05_case_E_weather_solar/02_bronze_to_silver_weather.ipynb",
        title=title,
        case=CASE,
        layer="bronce → plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_E,
    )


def _features(target: Path) -> Path:
    title = "Caso E · 03 Features meteorológicos para Caso B"
    sections = [
        section(
            1,
            "Objetivo",
            "Construir features meteorológicas reusables por el modelo de consumo del Caso B.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Lag/lead temporal de variables exógenas.\n"
            "- Dewpoint, sensación térmica.\n"
            "- Diurnal/seasonal encoding.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Caso B necesita `t_outdoor`, `ghi`, `dewpoint`, `is_daylight`.",
        ),
        section(4, "Relación con CENTINELA+", "Features se calculan al vuelo en producción."),
        section(5, "Relación con Medallion", "Lee plata, escribe oro."),
        section(6, "Datos de entrada", "Mock ERA5."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos y derivamos.",
            """\
csv_path = ROOT / "notebooks" / "_data" / "era5_xativa_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"]).set_index("timestamp")

def magnus_dewpoint(t, rh):
    a, b = 17.625, 243.04
    rh = np.clip(rh, 1, 100)
    alpha = np.log(rh / 100.0) + (a * t) / (b + t)
    return (b * alpha) / (a - alpha)

# RH no está en el mock; aproximamos con anti-correlación de T
rh_mock = np.clip(70 - (df["t_air_c"] - 18) * 1.5, 30, 90)
df["dewpoint_c"] = magnus_dewpoint(df["t_air_c"], rh_mock)
df["is_daylight"] = (df["ghi_w_m2"] > 50).astype(int)
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Estadísticas.",
            """\
print(df[["t_air_c", "ghi_w_m2", "dewpoint_c", "is_daylight"]].describe().round(2))
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Persistimos.",
            """\
out_dir = ROOT / "output" / "case_E"
out_dir.mkdir(parents=True, exist_ok=True)
parquet_path = out_dir / "weather_features.parquet"
df.to_parquet(parquet_path)
print(f"Wrote {parquet_path.relative_to(ROOT)}")
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Dewpoint vs T_air.",
            """\
plt.figure(figsize=(7, 3))
plt.scatter(df["t_air_c"], df["dewpoint_c"], s=4, color="#3F51B5")
plt.plot([0, 35], [0, 35], "--", color="gray")
plt.xlabel("T air (°C)"); plt.ylabel("Dewpoint (°C)")
plt.title("Dewpoint sigue a T_air pero queda por debajo")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Dewpoint <= T_air siempre.",
            """\
assert (df["dewpoint_c"] <= df["t_air_c"] + 0.5).all()
print("Sanity check OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Usar RH > 100 sin clip.\n"
            "2. Aplicar Magnus a T en K.\n"
            "3. Promediar `is_daylight` (categórica).",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `solar_zenith_angle`.\n"
            "2. Calcula `solar_irradiance_clear_sky` y compara.\n"
            "3. Estima `wind_chill`.",
        ),
        section(17, "Cómo se reutiliza con datos reales", "Idéntico — solo cambia origen."),
        common_summary(
            next_notebook="05_case_E_weather_solar/04_prediccion_solar.ipynb",
            docs_link="docs/use-cases/case-e-weather-solar.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="05_case_E_weather_solar/03_features_meteorologicas.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_E,
    )


def _prediccion(target: Path) -> Path:
    title = "Caso E · 04 Predicción solar — clear-sky decomposition + 3 baselines"
    sections = [
        section(
            1,
            "Objetivo",
            "Predecir `solar_irradiance` (GHI) **separando astronomía determinista de "
            "meteorología estocástica** (clear-sky decomposition). Comparar 4 modelos:\n\n"
            "1. **Persistencia 24 h**: $\\hat G(t) = G(t-24h)$.\n"
            "2. **Climatología por hora**: media histórica del valor a esa hora del día.\n"
            "3. **Clear-sky baseline**: $\\hat G(t) = G_{clear}(t) \\cdot 0.7$.\n"
            "4. **RF sobre clear-sky index** $k_c = G_{real}/G_{clear}$ predicho con XGB.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Por qué predecir $k_c$ es **mejor** que predecir GHI directo.\n"
            "- `np.clip(0)` y máscara nocturna para evitar irradiancias absurdas.\n"
            "- Skill score $1 - \\text{RMSE}_{\\text{model}}/\\text{RMSE}_{\\text{persistence}}$.\n"
            "- Diagnóstico 4-panel (timeline, scatter, residuos, CDF).",
        ),
        section(3, "Contexto del caso de uso", "Predicción solar es tool del chatbot."),
        section(4, "Relación con CENTINELA+", "Sirve a Caso B y Caso H."),
        section(5, "Relación con Medallion", "Oro: modelo entrenado + decomposición clear-sky."),
        section(6, "Datos de entrada", "Oro features Caso E."),
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Variables canónicas:\n\n"
            "| Variable CAPTIA | Rol |\n|---|---|\n"
            "| `solar_irradiance` | target (GHI W/m²) |\n"
            "| `temperature_outdoor` | feature meteorológica |\n",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos features.",
            """\
parquet_path = ROOT / "output" / "case_E" / "weather_features.parquet"
if parquet_path.exists():
    df = pd.read_parquet(parquet_path)
else:
    df, _ = mocks.make_era5_xativa_mock(days=90)
    df = df.set_index("timestamp")

X = pd.DataFrame(index=df.index)
X["hour"] = df.index.hour
X["doy"] = df.index.dayofyear
X["t"] = df["t_air_c"]
X["hour_sin"] = np.sin(2 * np.pi * X["hour"] / 24)
X["hour_cos"] = np.cos(2 * np.pi * X["hour"] / 24)
X["doy_sin"] = np.sin(2 * np.pi * X["doy"] / 365)
X["doy_cos"] = np.cos(2 * np.pi * X["doy"] / 365)
X["y"] = df["ghi_w_m2"]
X = X.dropna()
print({"filas": len(X), "rango_dias": (X.index.max() - X.index.min()).days})
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Computamos un **clear-sky model** simplificado (Iqbal 1983 reducido a "
            "geometría solar sin transmittance atmosférica detallada) y derivamos el "
            "clear-sky index $k_c$. Latitud Xátiva ≈ 38.99°N.",
            """\
LAT = np.deg2rad(38.99)
def clear_sky_ghi(idx):
    \"\"\"Clear-sky GHI simplificado: G_sc * cos(zenith) con cap superior.\"\"\"
    hour_frac = idx.hour + idx.minute / 60.0
    omega = np.deg2rad(15 * (hour_frac - 12))  # ángulo horario
    delta = np.deg2rad(23.45 * np.sin(2 * np.pi * (idx.dayofyear + 284) / 365))
    cos_z = np.sin(LAT) * np.sin(delta) + np.cos(LAT) * np.cos(delta) * np.cos(omega)
    g_clear = 1361 * np.maximum(cos_z, 0) * 0.75  # transmitancia clear-sky ~0.75
    return np.clip(g_clear, 0, 1100)

X["g_clear"] = clear_sky_ghi(X.index)
X["kc"] = (X["y"] / np.maximum(X["g_clear"], 1.0)).clip(0, 1.5)
X.loc[X["g_clear"] < 5, "kc"] = 0  # noche: kc indefinido
print({"kc_mean_diurno": float(X.loc[X["g_clear"] > 50, "kc"].mean()),
       "kc_p50_diurno": float(X.loc[X["g_clear"] > 50, "kc"].quantile(0.5))})
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "**4 modelos comparables** con clip(0) y máscara nocturna aplicada en "
            "predicción.",
            """\
from sklearn.ensemble import RandomForestRegressor
from notebooks._common.eval_helpers import (
    naive_persistence_24h, climatology_by_hour, mae as _mae, rmse as _rmse,
)

n = len(X); i = int(n * 0.7)
X_tr, X_te = X.iloc[:i], X.iloc[i:]
y_tr, y_te = X_tr["y"], X_te["y"]
g_clear_te = X_te["g_clear"]
night_mask_te = (g_clear_te < 5)

# (1) Persistencia 24h
y_persist = naive_persistence_24h(y_tr, y_te)

# (2) Climatología por hora
y_climat = climatology_by_hour(y_tr, y_te)

# (3) Clear-sky con kc=0.7 fijo
y_clear = (g_clear_te * 0.7).to_numpy()

# (4) RF sobre kc (predicción del clear-sky index)
features = ["t", "hour_sin", "hour_cos", "doy_sin", "doy_cos"]
diurno_tr = X_tr["g_clear"] > 5
m_kc = RandomForestRegressor(n_estimators=200, random_state=SEED, n_jobs=1).fit(
    X_tr.loc[diurno_tr, features], X_tr.loc[diurno_tr, "kc"]
)
kc_pred = m_kc.predict(X_te[features])
y_rf_kc = (kc_pred * g_clear_te.to_numpy()).clip(0)

# Aplicar máscara nocturna a TODOS los modelos
preds = {"persistencia_24h": y_persist, "climatologia_h": y_climat,
         "clear_sky_07": y_clear, "RF_kc": y_rf_kc}
for k in preds:
    preds[k] = np.where(night_mask_te, 0, np.clip(preds[k], 0, 1100))

table = pd.DataFrame({
    "model": list(preds.keys()),
    "RMSE": [_rmse(y_te.to_numpy(), p) for p in preds.values()],
    "MAE":  [_mae(y_te.to_numpy(), p) for p in preds.values()],
}).round(2)
rmse_persist = float(table.loc[table["model"] == "persistencia_24h", "RMSE"].iloc[0])
table["skill"] = (1 - table["RMSE"] / rmse_persist).round(3)
print(table)
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Diagnóstico 4-panel del mejor modelo (timeline + scatter + residuos + "
            "CDF errores) y comparativa skill por modelo.",
            """\
from notebooks._common.diagnostic_plots import plot_regression_diagnostic
import matplotlib.pyplot as plt

best_model = table.sort_values("RMSE").iloc[0]["model"]
y_best = preds[best_model]
plot_regression_diagnostic(
    y_te.to_numpy(), y_best,
    timestamps=y_te.index, title=f"Mejor modelo: {best_model}",
    sample_window=24*7,
)

plt.figure(figsize=(7, 3))
table.set_index("model")["skill"].plot.bar(color="#FF5722")
plt.axhline(0, color="gray", linestyle="--", label="persistencia (baseline)")
plt.title("Skill score vs persistencia 24h")
plt.legend(); plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "(a) Skill > 0 para al menos un modelo (algo bate persistencia). "
            "(b) GHI predicho ≥ 0 siempre (clip aplicado). "
            "(c) GHI nocturno = 0 (máscara aplicada).",
            """\
best = table.sort_values("RMSE").iloc[0]
assert best["skill"] > 0, f"Ningún modelo bate persistencia: best={best['model']} skill={best['skill']}"
for k, p in preds.items():
    assert (p >= 0).all(), f"{k}: predicciones negativas detectadas"
    assert (p[night_mask_te.to_numpy()] == 0).all(), f"{k}: predicciones nocturnas no = 0"
print(f"Validaciones OK · mejor modelo {best['model']} con skill={best['skill']:.3f}")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Predecir GHI directo** sin clear-sky decomposition: el modelo gasta "
            "capacidad reaprendiendo la astronomía solar.\n"
            "2. **Olvidar `clip(0)`**: regresores devuelven valores negativos en datos "
            "extremos. Físicamente imposible (irradiancia ≥ 0).\n"
            "3. **No aplicar máscara nocturna**: `g_clear` ya es 0 de noche, pero el "
            "modelo puede predecir +50 W/m² a las 3 AM si el dataset es ruidoso.\n"
            "4. **Train < 90 días**: estacionalidad anual no observable; el modelo "
            "extrapola mal a otra estación.\n"
            "5. **Skill score sin baseline**: reportar RMSE=120 W/m² no dice nada — "
            "comparar siempre contra persistencia y climatología.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Sustituye el clear-sky simplificado por `pvlib.clearsky.ineichen` y "
            "compara skill score. Rúbrica: skill ≥ +0.05 vs versión simplificada.\n"
            "2. Añade `cloud_cover` mock como feature al RF de $k_c$. ¿Mejora "
            "RMSE > 5 W/m²?\n"
            "3. Convierte GHI a producción FV (50 kWp, η=18 %, T_panel=T_air+25) y "
            "compara producción real vs predicha. Rúbrica: error diario < 10 %.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Mismo modelo, datos de ERA5 real o AEMET. Para FV añadir factor de "
            "rendimiento del panel + temperatura.",
        ),
        common_summary(
            next_notebook="06_case_F_mlops/01_mlflow_lakefs_overview.ipynb",
            docs_link="docs/use-cases/case-e-weather-solar.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="05_case_E_weather_solar/04_prediccion_solar.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_E,
    )


def build(target: Path) -> int:
    _eda(target)
    _bronze_silver(target)
    _features(target)
    _prediccion(target)
    return 4
