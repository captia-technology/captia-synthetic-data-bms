"""05 Case E — Meteorología y predicción de generación solar (4 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section

CASE = "E — Meteo & solar"
SPEC = "docs/specs/synthetic-bms/02-domain-spec.md"


def _eda(target: Path) -> Path:
    title = "Caso E · 01 EDA ERA5 Xàtiva (mock)"
    sections = [
        section(1, "Objetivo",
                "Conocer la estructura de ERA5 (mock 30 días Xàtiva) y derivar variables útiles "
                "para Caso B (forecast eléctrico) y Caso H (chatbot meteorológico)."),
        section(2, "Qué se aprende",
                "- Variables ERA5 horarias: T_air, GHI, viento, lluvia, presión.\n"
                "- Cómo descargar ERA5 real (CDS API) — fuera del repo.\n"
                "- Conversiones unitarias: K→°C, J/m²→W/m², m→mm.\n"
                "- Estacionalidad y diurnal cycle."),
        section(3, "Contexto del caso de uso",
                "ERA5 es el reanálisis climático global del ECMWF. Para Xàtiva tenemos un "
                "mock con 30 días horarios; el dataset real cubre desde 1940."),
        section(4, "Relación con CENTINELA+",
                "El dominio `weather_station/xativa/era5_gridpoint` complementa los "
                "edificios con variables externas correlacionadas."),
        section(5, "Relación con Medallion",
                "Bronce: NetCDF / mock CSV. Plata: `captia_point` con domain "
                "`weather_station`."),
        section(6, "Datos de entrada", "`era5_xativa_mock.csv`."),
        section(7, "Schema CAPTIA esperado",
                "Tags: `captia_env=dev`, `domain_id=weather_station`, `site_id=xativa`, "
                "`asset_id=era5_gridpoint`, `variable ∈ {temperature_outdoor, solar_irradiance, ...}`."),
        setup_section(),
        section(9, "Carga de datos o mock", "Cargamos mock.",
                """\
csv_path = ROOT / "notebooks" / "_data" / "era5_xativa_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
df.head()
"""),
        section(10, "Exploración paso a paso", "Estadísticas básicas y diurnal cycle.",
                """\
print(df.describe().round(2))
df["hour"] = df["timestamp"].dt.hour
df.groupby("hour")[["t_air_c", "ghi_w_m2"]].mean().round(2)
"""),
        section(11, "Transformación bronce → plata", "Notebook siguiente."),
        section(12, "Construcción de capa oro", "Notebook 03+04."),
        section(13, "Visualizaciones explicativas", "T y GHI horarios.",
                """\
fig, ax1 = plt.subplots(figsize=(10, 3))
ax1.plot(df["timestamp"], df["t_air_c"], color="#FF5722", label="T")
ax1.set_ylabel("°C")
ax2 = ax1.twinx()
ax2.plot(df["timestamp"], df["ghi_w_m2"], color="#FFC107", label="GHI")
ax2.set_ylabel("W/m²")
plt.title("Diurnal — Xàtiva mock 30 días")
plt.tight_layout()
"""),
        section(14, "Validaciones",
                "GHI nunca > 1100 W/m²; T entre -5 y 45.",
                """\
assert df["ghi_w_m2"].between(0, 1100).all()
assert df["t_air_c"].between(-5, 50).all()
print("Rangos OK")
"""),
        section(15, "Errores comunes",
                "1. Confundir GHI con DNI (Direct Normal Irradiance).\n"
                "2. Asumir que `pressure_hpa` es a nivel del mar (es local).\n"
                "3. Promediar viento sin orientación (vector vs escalar)."),
        section(16, "Ejercicios propuestos",
                "1. Calcula la insolación diaria (kWh/m²/día).\n"
                "2. Compara `t_air_c` con la curva esperada para Csa.\n"
                "3. Dibuja la rosa de los vientos."),
        section(17, "Cómo se reutiliza con datos reales",
                "Para descargar ERA5 real: registrarse en CDS, instalar `cdsapi`, "
                "ejecutar el script `scripts/era5_download.py` (no incluido)."),
        common_summary(next_notebook="05_case_E_weather_solar/02_bronze_to_silver_weather.ipynb",
                       docs_link="docs/use-cases/case-e-weather-solar.md"),
    ]
    return emit(target=target, rel_path="05_case_E_weather_solar/01_eda_era5.ipynb",
                title=title, case=CASE, layer="bronce", spec=SPEC, sections=sections)


def _bronze_silver(target: Path) -> Path:
    title = "Caso E · 02 ETL ERA5 → CAPTIA weather_station"
    sections = [
        section(1, "Objetivo",
                "Convertir el mock ERA5 a `captia_point` con `domain_id=weather_station`. "
                "Aplicar conversiones unitarias y validar rangos físicos."),
        section(2, "Qué se aprende",
                "- Conversión K→°C, J/m²→W/m², m→mm.\n"
                "- Cómo asignar `asset_id=era5_gridpoint`.\n"
                "- Validaciones físicas previas a la escritura."),
        section(3, "Contexto del caso de uso", "Los datos meteo se usan en B y H."),
        section(4, "Relación con CENTINELA+", "Site `xativa` independiente del aula."),
        section(5, "Relación con Medallion", "Bronce → plata."),
        section(6, "Datos de entrada", "`era5_xativa_mock.csv`."),
        section(7, "Schema CAPTIA esperado",
                "5 variables: `temperature_outdoor`, `solar_irradiance`, `wind_speed`, "
                "`precipitation`, `pressure`."),
        setup_section(),
        section(9, "Carga de datos o mock", "Cargamos.",
                """\
csv_path = ROOT / "notebooks" / "_data" / "era5_xativa_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
df.head()
"""),
        section(10, "Exploración paso a paso", "Mapping unidades.",
                """\
mapping = {
    "t_air_c": "temperature_outdoor",
    "ghi_w_m2": "solar_irradiance",
    "wind_speed_ms": "wind_speed",
    "precip_mm": "precipitation",
    "pressure_hpa": "pressure",
}
print(mapping)
"""),
        section(11, "Transformación bronce → plata", "Generamos line protocol.",
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
"""),
        section(12, "Construcción de capa oro", "Notebook 04."),
        section(13, "Visualizaciones explicativas", "Resumen anual sintético.",
                """\
df.set_index("timestamp")[["t_air_c", "ghi_w_m2"]].plot(figsize=(10, 3))
plt.title("ERA5 Xàtiva mock 30 días")
plt.tight_layout()
"""),
        section(14, "Validaciones", "Los rangos físicos se respetan en `captia_point_meta`.",
                """\
for csv_col, var in mapping.items():
    rmin, rmax = KNOWN_VARIABLES[var]["range"]
    s = df[csv_col]
    assert s.between(rmin - 5, rmax + 5).all(), f"{var} fuera de rango"
print("Rangos físicos OK")
"""),
        section(15, "Errores comunes",
                "1. Confundir `solar_irradiance` (GHI) con `solar_irradiance_dni`.\n"
                "2. No restar 273.15 si trabajas con K.\n"
                "3. Confundir tasa (J/s/m²) con energía acumulada (J/m²)."),
        section(16, "Ejercicios propuestos",
                "1. Añade `dewpoint` calculada con la fórmula de Magnus.\n"
                "2. Mapea `total_cloud_cover` (NetCDF real).\n"
                "3. Construye un downsample diario."),
        section(17, "Cómo se reutiliza con datos reales", "Cambiar el path al NetCDF real "
                "y `xarray.open_dataset` en vez de `pd.read_csv`."),
        common_summary(next_notebook="05_case_E_weather_solar/03_features_meteorologicas.ipynb",
                       docs_link="docs/contracts/variable-catalog.md"),
    ]
    return emit(target=target, rel_path="05_case_E_weather_solar/02_bronze_to_silver_weather.ipynb",
                title=title, case=CASE, layer="bronce → plata", spec=SPEC, sections=sections)


def _features(target: Path) -> Path:
    title = "Caso E · 03 Features meteorológicos para Caso B"
    sections = [
        section(1, "Objetivo",
                "Construir features meteorológicas reusables por el modelo de consumo "
                "del Caso B."),
        section(2, "Qué se aprende",
                "- Lag/lead temporal de variables exógenas.\n"
                "- Dewpoint, sensación térmica.\n"
                "- Diurnal/seasonal encoding."),
        section(3, "Contexto del caso de uso",
                "Caso B necesita `t_outdoor`, `ghi`, `dewpoint`, `is_daylight`."),
        section(4, "Relación con CENTINELA+", "Features se calculan al vuelo en producción."),
        section(5, "Relación con Medallion", "Lee plata, escribe oro."),
        section(6, "Datos de entrada", "Mock ERA5."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(9, "Carga de datos o mock", "Cargamos y derivamos.",
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
"""),
        section(10, "Exploración paso a paso", "Estadísticas.",
                """\
print(df[["t_air_c", "ghi_w_m2", "dewpoint_c", "is_daylight"]].describe().round(2))
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "Persistimos.",
                """\
out_dir = ROOT / "output" / "case_E"
out_dir.mkdir(parents=True, exist_ok=True)
parquet_path = out_dir / "weather_features.parquet"
df.to_parquet(parquet_path)
print(f"Wrote {parquet_path.relative_to(ROOT)}")
"""),
        section(13, "Visualizaciones explicativas",
                "Dewpoint vs T_air.",
                """\
plt.figure(figsize=(7, 3))
plt.scatter(df["t_air_c"], df["dewpoint_c"], s=4, color="#3F51B5")
plt.plot([0, 35], [0, 35], "--", color="gray")
plt.xlabel("T air (°C)"); plt.ylabel("Dewpoint (°C)")
plt.title("Dewpoint sigue a T_air pero queda por debajo")
plt.tight_layout()
"""),
        section(14, "Validaciones",
                "Dewpoint <= T_air siempre.",
                """\
assert (df["dewpoint_c"] <= df["t_air_c"] + 0.5).all()
print("Sanity check OK")
"""),
        section(15, "Errores comunes",
                "1. Usar RH > 100 sin clip.\n"
                "2. Aplicar Magnus a T en K.\n"
                "3. Promediar `is_daylight` (categórica)."),
        section(16, "Ejercicios propuestos",
                "1. Añade `solar_zenith_angle`.\n"
                "2. Calcula `solar_irradiance_clear_sky` y compara.\n"
                "3. Estima `wind_chill`."),
        section(17, "Cómo se reutiliza con datos reales", "Idéntico — solo cambia origen."),
        common_summary(next_notebook="05_case_E_weather_solar/04_prediccion_solar.ipynb",
                       docs_link="docs/use-cases/case-e-weather-solar.md"),
    ]
    return emit(target=target, rel_path="05_case_E_weather_solar/03_features_meteorologicas.ipynb",
                title=title, case=CASE, layer="oro", spec=SPEC, sections=sections)


def _prediccion(target: Path) -> Path:
    title = "Caso E · 04 Predicción de generación solar"
    sections = [
        section(1, "Objetivo",
                "Entrenar un regressor para `solar_irradiance` con T, hora del día y día del "
                "año. Punto de partida para predicción FV."),
        section(2, "Qué se aprende",
                "- Modelo simple de GHI con features físicas.\n"
                "- Métrica RMSE (W/m²).\n"
                "- Por qué la predicción solar a 24h es viable con buenos features."),
        section(3, "Contexto del caso de uso", "Predicción solar es tool del chatbot."),
        section(4, "Relación con CENTINELA+", "Sirve a Caso B y Caso H."),
        section(5, "Relación con Medallion", "Oro: modelo entrenado."),
        section(6, "Datos de entrada", "Oro features Caso E."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(9, "Carga de datos o mock", "Cargamos.",
                """\
parquet_path = ROOT / "output" / "case_E" / "weather_features.parquet"
if parquet_path.exists():
    df = pd.read_parquet(parquet_path)
else:
    df, _ = mocks.make_era5_xativa_mock()
    df = df.set_index("timestamp")

X = pd.DataFrame(index=df.index)
X["hour"] = df.index.hour
X["doy"] = df.index.dayofyear
X["t"] = df["t_air_c"]
X["hour_sin"] = np.sin(2 * np.pi * X["hour"] / 24)
X["hour_cos"] = np.cos(2 * np.pi * X["hour"] / 24)
X["y"] = df["ghi_w_m2"]
X = X.dropna()
print(X.shape)
"""),
        section(10, "Exploración paso a paso", "Split temporal.",
                """\
n = len(X)
i = int(n * 0.7)
X_tr, X_te = X.iloc[:i], X.iloc[i:]
y_tr, y_te = X_tr.pop("y"), X_te.pop("y")
"""),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro",
                "Modelo y métrica.",
                """\
from sklearn.ensemble import RandomForestRegressor

m = RandomForestRegressor(n_estimators=200, random_state=SEED).fit(X_tr, y_tr)
y_pred = m.predict(X_te)
rmse = float(np.sqrt(np.mean((y_te.values - y_pred) ** 2)))
print({"RMSE_W_m2": round(rmse, 2)})
"""),
        section(13, "Visualizaciones explicativas",
                "Curva real vs predicción 7 días.",
                """\
plt.figure(figsize=(10, 3))
plt.plot(y_te.index[:24*7], y_te.values[:24*7], label="real", color="#FF5722")
plt.plot(y_te.index[:24*7], y_pred[:24*7], label="modelo", color="#3F51B5")
plt.legend(); plt.title("GHI predicho 7 días")
plt.tight_layout()
"""),
        section(14, "Validaciones",
                "RMSE < 200 W/m² aceptable para clase.",
                """\
assert rmse < 250
"""),
        section(15, "Errores comunes",
                "1. **Olvidar ciclo anual** (dayofyear).\n"
                "2. **Predecir GHI nocturno** distinto de cero.\n"
                "3. **No clip a 0**."),
        section(16, "Ejercicios propuestos",
                "1. Añade `cloud_cover` (mock razonable).\n"
                "2. Convierte GHI a Wh/día y compara con energía esperada FV.\n"
                "3. Ensaya XGBoost y compara."),
        section(17, "Cómo se reutiliza con datos reales",
                "Mismo modelo, datos de ERA5 real o AEMET. Para FV añadir factor de "
                "rendimiento del panel + temperatura."),
        common_summary(next_notebook="06_case_F_mlops/01_mlflow_lakefs_overview.ipynb",
                       docs_link="docs/use-cases/case-e-weather-solar.md"),
    ]
    return emit(target=target, rel_path="05_case_E_weather_solar/04_prediccion_solar.ipynb",
                title=title, case=CASE, layer="oro", spec=SPEC, sections=sections)


def build(target: Path) -> int:
    _eda(target)
    _bronze_silver(target)
    _features(target)
    _prediccion(target)
    return 4
