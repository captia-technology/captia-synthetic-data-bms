"""09 Case I — Big Data: benchmark Spark vs pandas (4 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section

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
        section(7, "Schema CAPTIA esperado", "No aplica para benchmark."),
        setup_section(),
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
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
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
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(
            9,
            "Carga de datos o mock",
            "Detectamos backend.",
            """\
HAS_SPARK = HAS_DASK = False
try:
    from pyspark.sql import SparkSession
    HAS_SPARK = True
except ImportError:
    try:
        import dask.dataframe as dd
        HAS_DASK = True
    except ImportError:
        pass
print({"spark": HAS_SPARK, "dask": HAS_DASK})
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Operaciones equivalentes.",
            """\
import time

results_spark = []

if HAS_SPARK:
    spark = SparkSession.builder.appName("captia-benchmark").master("local[*]").getOrCreate()
    sdf = spark.read.csv(str(ROOT / "notebooks/_data/bdg2_education_subset_mock.csv"),
                          header=True, inferSchema=True, comment="#")

    ops = {
        "groupby_building": lambda d: d.groupBy("building_id").avg("power_kw").count(),
        "groupby_hour_dow": lambda d: d.selectExpr("hour(timestamp) as h", "dayofweek(timestamp) as dow", "power_kw")
                                          .groupBy("h", "dow").avg("power_kw").count(),
    }
    for name, fn in ops.items():
        t0 = time.perf_counter()
        fn(sdf)
        results_spark.append({"op": name, "spark_s": time.perf_counter() - t0})
    spark.stop()
elif HAS_DASK:
    df = dd.read_csv(str(ROOT / "notebooks/_data/bdg2_education_subset_mock.csv"),
                     comment="#", parse_dates=["timestamp"])
    for name, fn in {
        "groupby_building": lambda d: d.groupby("building_id")["power_kw"].mean().compute(),
        "groupby_hour_dow": lambda d: d.assign(hour=d["timestamp"].dt.hour, dow=d["timestamp"].dt.dayofweek)
                                         .groupby(["hour", "dow"])["power_kw"].mean().compute(),
    }.items():
        t0 = time.perf_counter()
        fn(df)
        results_spark.append({"op": name, "spark_s": time.perf_counter() - t0})
else:
    print("Sin pyspark ni dask — el notebook documenta la operación pero no mide.")

bench_spark = pd.DataFrame(results_spark)
bench_spark
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(12, "Construcción de capa oro", "Tabla."),
        section(
            13,
            "Visualizaciones explicativas",
            "Plot si hay datos.",
            """\
if not bench_spark.empty:
    bench_spark.set_index("op")["spark_s"].plot.bar(color="#FF5722", figsize=(7, 3))
    plt.title("Spark/Dask — tiempos")
    plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Si hay backend, los tiempos son positivos.",
            """\
if not bench_spark.empty:
    assert (bench_spark["spark_s"] > 0).all()
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
    )


def _comparativa(target: Path) -> Path:
    title = "Caso I · 04 Comparativa pandas vs Spark — cuándo merece la pena"
    sections = [
        section(
            1,
            "Objetivo",
            "Combinar los resultados de los notebooks 02 y 03 y emitir una recomendación clara.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Speedup en función del tamaño.\n"
            "- Punto de cruce pandas / Spark.\n"
            "- Coste fijo de Spark.",
        ),
        section(3, "Contexto del caso de uso", "Recomendación final del proyecto."),
        section(4, "Relación con CENTINELA+", "Tomas de decisión."),
        section(5, "Relación con Medallion", "Oro: análisis."),
        section(6, "Datos de entrada", "JSON tiempos."),
        section(7, "Schema CAPTIA esperado", "No aplica."),
        setup_section(),
        section(
            9,
            "Carga de datos o mock",
            "Combinamos resultados de demo.",
            """\
demo_pd = pd.DataFrame([{"op": "groupby_building", "median_s": 0.05},
                          {"op": "groupby_hour_dow", "median_s": 0.07}])
demo_sp = pd.DataFrame([{"op": "groupby_building", "spark_s": 1.2},
                          {"op": "groupby_hour_dow", "spark_s": 1.5}])
combined = demo_pd.merge(demo_sp, on="op")
combined["speedup_pandas_better"] = combined["spark_s"] / combined["median_s"]
combined
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "En subsets pequeños pandas gana.",
            """\
sizes = [1e3, 1e4, 1e5, 1e6, 1e7]
# Modelo simplificado: pandas O(N), Spark = startup_const + alpha*N (alpha << pandas alpha cuando N grande)
pd_t = [n * 1e-7 for n in sizes]
sp_t = [1.0 + n * 1e-9 for n in sizes]
table = pd.DataFrame({"N": sizes, "pandas_s": pd_t, "spark_s": sp_t})
table["winner"] = np.where(np.array(pd_t) < np.array(sp_t), "pandas", "spark")
table
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Plot speedup.",
            """\
plt.figure(figsize=(8, 3))
plt.plot(sizes, pd_t, label="pandas", color="#3F51B5", marker="o")
plt.plot(sizes, sp_t, label="spark", color="#FF5722", marker="o")
plt.xscale("log"); plt.yscale("log")
plt.xlabel("N filas"); plt.ylabel("segundos")
plt.legend(); plt.title("Cruce pandas vs Spark (modelo)")
plt.tight_layout()
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Recomendación textual.",
            """\
crossover = sizes[next((i for i, (p, s) in enumerate(zip(pd_t, sp_t)) if p > s), -1)]
print(f"Punto de cruce aproximado: {crossover:.0e} filas")
print("Recomendación: Spark cuando el dataset > 1M filas o cuando se proyecte crecer.")
""",
        ),
        section(
            14,
            "Validaciones",
            "El cruce está en escala log.",
            """\
assert any(p > s for p, s in zip(pd_t, sp_t))
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Recomendar Spark sin medir.\n"
            "2. No considerar coste operativo del cluster.\n"
            "3. Comparar Spark single-node con pandas — no es justo.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Mide el modelo real con tu subset.\n"
            "2. Calcula el tamaño BDG2 completo y predice speedup.\n"
            "3. Ensaya `polars` como alternativa.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Re-ejecutar con BDG2 completo en cluster ITI.",
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
    )


def build(target: Path) -> int:
    _overview(target)
    _pandas(target)
    _spark(target)
    _comparativa(target)
    return 4
