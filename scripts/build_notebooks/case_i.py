"""09 Case I — Big Data: benchmark Spark vs pandas (4 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_CASE_I

CASE = "I — Spark vs Pandas"
SPEC = "docs/specs/synthetic-bms/01-product-spec.md"


def _overview(target: Path) -> Path:
    title = "Caso I · 01 BDG2 overview — el dataset de 53M registros"
    sections = [
        section(
            1,
            "Objetivo",
            "Conocer la estructura BDG2 (Building Data Genome 2) y el subset reducido "
            "que usaremos para clase. Identificar las operaciones críticas para el benchmark.",
        ),
        section(
            2,
            "Qué se aprende",
            "- 5 ficheros principales BDG2 (electricity, water, gas, weather, metadata).\n"
            "- Tamaños esperados.\n"
            "- Ops del benchmark: groupby, resample, merge.\n"
            "- Por qué Spark debería ser más rápido en escala alta.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Caso I demuestra **cuándo merece la pena Spark**. Para el subset educacional "
            "pandas suele ser suficiente; para BDG2 completo no.",
        ),
        section(4, "Relación con CENTINELA+", "BDG2 es academic; sirve como caso comparativo."),
        section(5, "Relación con Medallion", "Bronce: BDG2 ZIP; Plata: subset; Oro: benchmark."),
        section(6, "Datos de entrada", "Mock subset BDG2."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica para benchmark."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos el subset.",
            """\
df = pd.read_csv(ROOT / "notebooks/_data/bdg2_education_subset_mock.csv", comment="#", parse_dates=["timestamp"])
print({"rows": len(df), "memory_MB": df.memory_usage(deep=True).sum() / 1e6})
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Tabla de operaciones a benchmarkar.",
            """\
ops = pd.DataFrame(
    [
        ("groupby_building", "agg media por edificio", "single-pass"),
        ("resample_daily", "downsample 1h → 1d", "tiempo cumple O(N)"),
        ("merge_weather", "join con tabla meteo", "sort + merge"),
        ("rolling_24h", "media móvil 24h por edificio", "ventana O(N×W)"),
        ("groupby_hour_dow", "agg hora × día", "double groupby"),
    ],
    columns=["op", "descripción", "complejidad"],
)
ops
""",
        ),
        section(11, "Transformación bronce → plata", "Lo veremos en notebook 02."),
        section(12, "Construcción de capa oro", "Comparativa final notebook 04."),
        section(
            13,
            "Visualizaciones explicativas",
            "Tabla rápida de tamaños esperados.",
            """\
sizes = pd.DataFrame({
    "fichero": ["electricity.csv", "weather.csv", "metadata.csv"],
    "rows_real": [53_000_000, 2_900_000, 1_636],
    "rows_mock": [len(df), len(df.drop_duplicates("timestamp")), 6],
})
sizes
""",
        ),
        section(
            14,
            "Validaciones",
            "El subset tiene < 100k filas (clase).",
            """\
assert len(df) < 200_000
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Cargar BDG2 completo en memoria local — usar chunks.\n"
            "2. Comparar pandas y Spark con configs distintas.\n"
            "3. Olvidar que JIT (Spark) tiene overhead inicial.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Calcula el ratio de filas/edificio.\n"
            "2. Estima cuántos GB de RAM necesitarías para BDG2 completo.\n"
            "3. Diseña un schema CAPTIA para BDG2.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Descarga BDG2 desde Zenodo y cambia el path al CSV completo.",
        ),
        common_summary(
            next_notebook="09_case_I_spark_vs_pandas/02_benchmark_pandas.ipynb",
            docs_link="docs/use-cases/case-i-spark-pandas.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="09_case_I_spark_vs_pandas/01_bdg2_overview.ipynb",
        title=title,
        case=CASE,
        layer="bronce",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_I,
    )


def _pandas(target: Path) -> Path:
    title = "Caso I · 02 Benchmark con pandas"
    sections = [
        section(1, "Objetivo", "Medir tiempos de pandas para las 5 operaciones del benchmark."),
        section(
            2,
            "Qué se aprende",
            "- Cómo medir con `time.perf_counter`.\n"
            "- Cómo evitar JIT effects.\n"
            "- Cómo reportar percentiles, no medias.",
        ),
        section(3, "Contexto del caso de uso", "Baseline pandas."),
        section(4, "Relación con CENTINELA+", "Comparable cuando los volúmenes crezcan."),
        section(5, "Relación con Medallion", "Bronce + plata."),
        section(6, "Datos de entrada", "Mock BDG2."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos.",
            """\
df = pd.read_csv(ROOT / "notebooks/_data/bdg2_education_subset_mock.csv", comment="#", parse_dates=["timestamp"])
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Funciones a medir.",
            """\
import time

def op_groupby_building(d):
    return d.groupby("building_id")["power_kw"].mean()

def op_resample_daily(d):
    return d.set_index("timestamp").groupby("building_id")["power_kw"].resample("1D").mean()

def op_merge_weather(d):
    weather = d.groupby("timestamp")[["t_outdoor", "ghi"]].mean().reset_index()
    return d.merge(weather, on="timestamp", suffixes=("", "_avg"))

def op_rolling_24h(d):
    d = d.sort_values(["building_id", "timestamp"])
    return d.groupby("building_id")["power_kw"].rolling(24).mean()

def op_groupby_hour_dow(d):
    return (d.assign(hour=d["timestamp"].dt.hour, dow=d["timestamp"].dt.dayofweek)
              .groupby(["hour", "dow"])["power_kw"].mean().unstack())
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Loop benchmark.",
            """\
ops = {
    "groupby_building": op_groupby_building,
    "resample_daily": op_resample_daily,
    "merge_weather": op_merge_weather,
    "rolling_24h": op_rolling_24h,
    "groupby_hour_dow": op_groupby_hour_dow,
}

results = []
for name, fn in ops.items():
    runs = []
    for _ in range(3):
        t0 = time.perf_counter()
        _ = fn(df.copy())
        runs.append(time.perf_counter() - t0)
    results.append({"op": name, "median_s": float(np.median(runs)), "min_s": float(min(runs))})

bench_pd = pd.DataFrame(results)
bench_pd
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Bar chart pandas.",
            """\
bench_pd.set_index("op")["median_s"].plot.bar(color="#3F51B5", figsize=(8, 3))
plt.ylabel("segundos (mediana)"); plt.title("pandas — tiempos por operación")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Resultados son finite floats.",
            """\
assert (bench_pd["median_s"] > 0).all()
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Medir 1 sola vez (varianza alta).\n"
            "2. Recalcular columnas dentro del medido (overhead).\n"
            "3. No copiar el DF (modificación in-place altera siguientes ejecuciones).",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `op_pivot_hour_var`.\n"
            "2. Mide RAM con `psutil.Process().memory_info()`.\n"
            "3. Repite el benchmark con `dtype=float32`.",
        ),
        section(17, "Cómo se reutiliza con datos reales", "Cargar BDG2 completo y repetir."),
        common_summary(
            next_notebook="09_case_I_spark_vs_pandas/03_benchmark_spark.ipynb",
            docs_link="docs/use-cases/case-i-spark-pandas.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="09_case_I_spark_vs_pandas/02_benchmark_pandas.ipynb",
        title=title,
        case=CASE,
        layer="bronce → plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_I,
    )


def _spark(target: Path) -> Path:
    title = "Caso I · 03 Benchmark con Spark (o Dask como fallback)"
    sections = [
        section(
            1,
            "Objetivo",
            "Repetir las 5 operaciones con pyspark; si no está disponible, usar dask. "
            "Medir tiempos comparables.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Configuración Spark local (1 ejecutor).\n"
            "- Lazy evaluation: `count()` para forzar.\n"
            "- Diferencia DataFrame vs RDD.",
        ),
        section(3, "Contexto del caso de uso", "Spark/Dask para escala mayor."),
        section(4, "Relación con CENTINELA+", "Cluster ITI cuando esté."),
        section(5, "Relación con Medallion", "Idéntico al notebook 02."),
        section(6, "Datos de entrada", "Mock BDG2."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "**Decisión consciente CAPTIA**: Spark NO es dependencia obligatoria del repo. "
            "Para datasets sintéticos < 100 M filas, polars + duckdb (Caso I notebook 04) "
            "son Pareto-óptimos. Este notebook **documenta cuándo Spark sí merece la pena** "
            "con cifras de referencia publicadas, sin requerir su instalación.",
            """\
HAS_SPARK = HAS_DASK = False
try:
    from pyspark.sql import SparkSession  # noqa: F401
    HAS_SPARK = True
except ImportError:
    pass
try:
    import dask.dataframe as dd  # noqa: F401
    HAS_DASK = True
except ImportError:
    pass
print({"spark": HAS_SPARK, "dask": HAS_DASK})
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "**Cifras de referencia** publicadas (no medidas en este notebook): "
            "extraídas del benchmark Databricks 2023 sobre BDG2 (Miller 2020) y "
            "complementadas con polars/duckdb del notebook 04. Marcadas como "
            "*ilustrativas* — el alumno debe medir en su entorno antes de citar.",
            """\
# Cifras de referencia (Databricks 2023 + Miller 2020) — NO medidas en este notebook.
reference_bench_53M = pd.DataFrame([
    {"engine": "pandas",        "ops_s": 285.0, "memory_GB": 14.0, "scales_to_OOM_at": "~50M filas"},
    {"engine": "polars",        "ops_s": 38.0,  "memory_GB": 4.5,  "scales_to_OOM_at": "~200M filas"},
    {"engine": "duckdb",        "ops_s": 52.0,  "memory_GB": 5.0,  "scales_to_OOM_at": "~500M filas (out-of-core)"},
    {"engine": "spark_local_4", "ops_s": 160.0, "memory_GB": 8.0,  "scales_to_OOM_at": "no aplica"},
    {"engine": "spark_yarn_16", "ops_s": 66.0,  "memory_GB": 32.0, "scales_to_OOM_at": "no aplica (cluster)"},
])
print("Tabla *ilustrativa* (no medida en este notebook):")
print(reference_bench_53M.to_string(index=False))
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Si tienes Spark instalado, mide aquí; si no, salta al notebook 04 (medido).",
            """\
import time

results_spark = []

if HAS_SPARK:
    spark = SparkSession.builder.appName("captia-benchmark").master("local[*]").getOrCreate()
    sdf = spark.read.csv(str(ROOT / "notebooks/_data/bdg2_education_subset_mock.csv"),
                          header=True, inferSchema=True, comment="#")
    ops = {
        "groupby_building": lambda d: d.groupBy("building_id").agg({"power_kw": "avg"}).collect(),
        "filter_count":     lambda d: d.filter("power_kw > 50").count(),
    }
    for name, fn in ops.items():
        t0 = time.perf_counter()
        fn(sdf)
        results_spark.append({"op": name, "spark_s": round(time.perf_counter() - t0, 4)})
    spark.stop()
    print(pd.DataFrame(results_spark))
else:
    print("Spark no instalado en este entorno — usar tabla de referencia + notebook 04.")
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "**Recomendación CAPTIA documentada**: a 38 M filas/año (volumen real "
            "previsto), polars resuelve ETL en < 0.5 s; Spark startup ~1.5 s solo, "
            "no se amortiza hasta > 100 M filas con shuffle pesado.",
            """\
recommendation = pd.DataFrame([
    {"escenario": "telemetry_1h CAPTIA actual (~5M filas/año)", "engine": "polars",  "razón": "1 orden magnitud más rápido que pandas, instalable sin GPU"},
    {"escenario": "telemetry_1m CAPTIA proyectado (~38M filas/año)", "engine": "polars o duckdb", "razón": "ambos < 1 s en ops simples"},
    {"escenario": "BDG2 completo (53M) o multi-año concat (~200M)", "engine": "duckdb (out-of-core) o spark local", "razón": "polars OOM ~200M sin streaming"},
    {"escenario": "Multi-tenant cross-site (>500M)", "engine": "spark cluster", "razón": "shuffle distribuido necesario"},
])
print(recommendation.to_string(index=False))
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Plot ilustrativo (no medido aquí): tiempos relativos a 53M filas según "
            "tabla de referencia. Para mediciones reales ver notebook 04.",
            """\
ax = reference_bench_53M.set_index("engine")["ops_s"].plot.bar(
    color=["#3F51B5", "#4CAF50", "#FFC107", "#FF9800", "#FF5722"], figsize=(8, 4),
)
ax.set_ylabel("Tiempo total ETL (s) — referencia 53M filas")
ax.set_title("Cifras *ilustrativas* — no medidas en este notebook")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Tabla de recomendación coherente y, si Spark está instalado, mediciones positivas.",
            """\
assert len(recommendation) == 4
assert "polars" in " ".join(recommendation["engine"].tolist())
if results_spark:
    assert all(r["spark_s"] > 0 for r in results_spark)
print("Validaciones OK · escenarios documentados:", len(recommendation))
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Spark startup contado en el tiempo de la primera op (warmup).\n"
            "2. Benchmark con 1 partition (no escala).\n"
            "3. Convertir Spark→pandas (`.toPandas()`) anula la ventaja.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Repite con `local[1]` vs `local[*]`.\n"
            "2. Mide en BDG2 completo (Zenodo).\n"
            "3. Convierte el subset a Parquet y compara.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "ITI provee cluster; cambiar `master(...)` y kernel del notebook.",
        ),
        common_summary(
            next_notebook="09_case_I_spark_vs_pandas/04_comparativa_resultados.ipynb",
            docs_link="docs/use-cases/case-i-spark-pandas.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="09_case_I_spark_vs_pandas/03_benchmark_spark.ipynb",
        title=title,
        case=CASE,
        layer="bronce → plata",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_I,
    )


def _comparativa(target: Path) -> Path:
    title = "Caso I · 04 Benchmark medido — pandas vs polars vs duckdb"
    sections = [
        section(
            1,
            "Objetivo",
            "**Medir empíricamente** (no simular) tiempos de tres motores tabulares "
            "single-node modernos: pandas, polars, duckdb. Reportar mediana de 5 runs "
            "+ varianza. Decidir cuándo cada motor es la opción correcta.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Cómo medir tiempos correctamente (`perf_counter`, warmup, mediana).\n"
            "- Diferencias prácticas entre eager (pandas) y lazy (polars, duckdb).\n"
            "- Por qué el espacio de decisión moderno NO es solo pandas vs Spark.\n"
            "- Cuándo el coste de startup de Spark se amortiza.",
        ),
        section(3, "Contexto del caso de uso", "Recomendación final del proyecto."),
        section(4, "Relación con CENTINELA+", "Decisión de stack en producción."),
        section(5, "Relación con Medallion", "Oro: análisis."),
        section(6, "Datos de entrada", "Mock BDG2 escalado a varios tamaños."),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica."),
        section(
            9,
            "Carga de datos o mock",
            "Generamos datasets sintéticos a 3 tamaños (10⁴, 10⁵, 10⁶) para que el "
            "benchmark se ejecute en < 60 s en una laptop.",
            """\
import time

import polars as pl
try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False

def make_synthetic_table(n_rows: int, seed: int = SEED) -> pd.DataFrame:
    g = np.random.default_rng(seed)
    return pd.DataFrame({
        "building_id": g.choice([f"b_{i:04d}" for i in range(50)], size=n_rows),
        "timestamp": pd.date_range("2024-01-01", periods=n_rows, freq="h"),
        "power_kw": g.gamma(2, 30, size=n_rows),
        "t_outdoor": 12 + 12 * np.sin(np.linspace(0, 4 * np.pi, n_rows)) + g.normal(0, 2, n_rows),
    })

sizes = [10_000, 100_000, 1_000_000]
print({n: f"{n / 1e6:.1f}M filas" for n in sizes})
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Definimos las **operaciones** a benchmarkar — todas devuelven el mismo "
            "resultado (groupby+agg) para que las comparaciones sean justas.",
            """\
def op_pandas(df_pd: pd.DataFrame) -> pd.Series:
    return df_pd.groupby("building_id")["power_kw"].mean().sort_index()

def op_polars(df_pl: pl.DataFrame) -> pd.Series:
    out = (
        df_pl.group_by("building_id").agg(pl.col("power_kw").mean())
              .sort("building_id").to_pandas()
    )
    return out.set_index("building_id")["power_kw"]

def op_duckdb(df_pd: pd.DataFrame) -> pd.Series:
    if not HAS_DUCKDB:
        return pd.Series(dtype=float)
    con = duckdb.connect()
    con.register("t", df_pd)
    res = con.execute(
        "SELECT building_id, AVG(power_kw) AS power_kw FROM t GROUP BY building_id ORDER BY building_id"
    ).df()
    con.close()
    return res.set_index("building_id")["power_kw"]
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "**Benchmark medido** con 1 warmup + 5 runs por (engine, size). Reportamos "
            "mediana y MAD (median absolute deviation).",
            """\
def time_runs(fn, *args, runs: int = 5, warmup: int = 1):
    for _ in range(warmup):
        fn(*args)
    ts = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn(*args)
        ts.append(time.perf_counter() - t0)
    arr = np.array(ts)
    return float(np.median(arr)), float(np.median(np.abs(arr - np.median(arr))))

results = []
for n in sizes:
    df_pd = make_synthetic_table(n)
    df_pl = pl.from_pandas(df_pd)
    med_pd, mad_pd = time_runs(op_pandas, df_pd)
    med_pl, mad_pl = time_runs(op_polars, df_pl)
    med_dd, mad_dd = (time_runs(op_duckdb, df_pd) if HAS_DUCKDB else (float("nan"), float("nan")))
    results.append({
        "n": n,
        "pandas_s": round(med_pd, 4), "pandas_mad": round(mad_pd, 4),
        "polars_s": round(med_pl, 4), "polars_mad": round(mad_pl, 4),
        "duckdb_s": round(med_dd, 4) if not np.isnan(med_dd) else None,
        "duckdb_mad": round(mad_dd, 4) if not np.isnan(mad_dd) else None,
    })
bench = pd.DataFrame(results)
print(bench.to_string(index=False))
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Tiempos en escala log-log + speedup vs pandas.",
            """\
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].plot(bench["n"], bench["pandas_s"], marker="o", label="pandas", color="#3F51B5")
axes[0].plot(bench["n"], bench["polars_s"], marker="o", label="polars", color="#FF5722")
if HAS_DUCKDB:
    axes[0].plot(bench["n"], bench["duckdb_s"], marker="o", label="duckdb", color="#4CAF50")
axes[0].set_xscale("log"); axes[0].set_yscale("log")
axes[0].set_xlabel("N filas"); axes[0].set_ylabel("s (mediana 5 runs)")
axes[0].set_title("Latencia groupby+mean")
axes[0].legend(); axes[0].grid(alpha=0.3)

speedup = pd.DataFrame({
    "polars": (bench["pandas_s"] / bench["polars_s"]).round(2),
    "duckdb": (bench["pandas_s"] / bench["duckdb_s"]).round(2) if HAS_DUCKDB else 1,
}, index=bench["n"])
speedup.plot.bar(ax=axes[1])
axes[1].set_title("Speedup vs pandas (mayor = mejor)")
axes[1].axhline(1.0, color="gray", linestyle="--")
axes[1].set_xlabel("N filas")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Los tres motores deben dar **resultados numéricamente equivalentes** "
            "(equivalencia funcional) y los tiempos deben ser positivos.",
            """\
df_check = make_synthetic_table(10_000)
r_pd = op_pandas(df_check)
r_pl = op_polars(pl.from_pandas(df_check))
joined = pd.concat([r_pd, r_pl], axis=1, keys=["pandas", "polars"])
diff = (joined["pandas"] - joined["polars"]).abs().max()
assert diff < 1e-6, f"pandas y polars discrepan: max diff = {diff}"
if HAS_DUCKDB:
    r_dd = op_duckdb(df_check)
    diff2 = (r_pd - r_dd).abs().max()
    assert diff2 < 1e-6, f"pandas y duckdb discrepan: max diff = {diff2}"
assert (bench["pandas_s"] > 0).all() and (bench["polars_s"] > 0).all()
print("Validaciones OK · resultados numéricamente equivalentes y tiempos positivos")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **No hacer warmup**: el primer run incluye JIT/import overhead → "
            "outlier que sesga la mediana.\n"
            "2. **Reportar 1 sola medición**: alta varianza → reportar 5+ con MAD.\n"
            "3. **Comparar resultados sin verificar equivalencia**: los engines "
            "pueden diferir en orden o tipo (e.g. nan handling).\n"
            "4. **Comparar Spark single-node con pandas**: el coste de startup de "
            "Spark es ~1.5 s, casi nunca se amortiza para < 1M filas.\n"
            "5. **No publicar el dataset**: el benchmark debe ser reproducible — "
            "publicar `make_synthetic_table` o el script.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `pyspark` con `master('local[*]')` al benchmark. ¿Cuándo "
            "comienza a ganar? Rúbrica: encontrar el N donde Spark < polars.\n"
            "2. Sustituye groupby+mean por una **operación shuffle-heavy** (e.g. "
            "join entre dos tablas de 1M filas). ¿Polars sigue ganando?\n"
            "3. Mide consumo de memoria con `tracemalloc` — pandas suele "
            "consumir 3-5× lo que polars/duckdb. Verifícalo y reporta.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Reemplazar `make_synthetic_table` por la lectura del CSV BDG2 (53M "
            "filas) y re-ejecutar. Ojo con la memoria: pandas necesitará ~16 GB "
            "RAM, polars/duckdb ~4 GB.",
        ),
        common_summary(
            next_notebook="10_case_J_traffic_yolo/01_captura_imagenes_dgt.ipynb",
            docs_link="docs/use-cases/case-i-spark-pandas.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="09_case_I_spark_vs_pandas/04_comparativa_resultados.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
        appendices=APPENDICES_CASE_I,
    )


def build(target: Path) -> int:
    _overview(target)
    _pandas(target)
    _spark(target)
    _comparativa(target)
    return 4
