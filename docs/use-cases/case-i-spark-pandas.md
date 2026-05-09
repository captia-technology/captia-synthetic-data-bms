# Caso I — Big Data: benchmark Spark vs pandas

> **Última verificación:** 2026-05-10
> **Audiencia:** equipo G2 (Oscar, Vicent, David).
> **Capa Medallion primaria:** bronce → plata.
> **Notebooks:** 4 (`notebooks/09_case_I_spark_vs_pandas/`).

## Objetivo

Demostrar empíricamente las ventajas del procesamiento distribuido con
Spark frente a pandas sobre el dataset BDG2 completo (~53M filas) y
construir el subset reducido que el Caso B usa.

## Datos esperados

- **Bronce primario:** BDG2 (Zenodo / Kaggle). Mock subset 6 edif × 12 m
  horarios en `notebooks/_data/bdg2_education_subset_mock.csv`.

## Capas Medallion

| Capa | Contenido |
|---|---|
| Bronce | BDG2 ZIP completo o subset CSV |
| Plata | subset reducido (5–10 edificios × 12 meses) cargado a InfluxDB para Caso B |
| Oro | benchmark + recomendación |

## Notebooks asociados

1. `01_bdg2_overview.ipynb` — estructura, tamaños, ops.
2. `02_benchmark_pandas.ipynb` — tiempos pandas.
3. `03_benchmark_spark.ipynb` — tiempos Spark (o Dask como fallback).
4. `04_comparativa_resultados.ipynb` — speedup vs N, recomendación.

## Operaciones medidas

- `groupby_building` — agg media por edificio.
- `resample_daily` — downsample horario → diario.
- `merge_weather` — join con meteo.
- `rolling_24h` — media móvil.
- `groupby_hour_dow` — agg hora × día.

## Validación

- Tiempos finitos > 0 para cada op en cada backend disponible.
- Spark vs pandas converge en el cruce esperado (~1M filas).
- Resultado numéricamente equivalente entre backends.

## Errores comunes

1. **Spark single-node con datasets pequeños** — pandas siempre gana.
2. **Comparar configs distintas** (1 worker vs *).
3. **Convertir Spark→pandas** dentro del benchmark (anula la ventaja).
4. **Usar `iloc` en Spark** — no existe.

## Reutilización con datos reales

Los notebooks aceptan BDG2 completo (cambia el path). Para producción ITI:

```python
spark = SparkSession.builder \
    .master("yarn") \
    .config("spark.executor.instances", "10") \
    .getOrCreate()
```

## Coordinación con otros casos

- **Caso B** (G1) — recibe el subset educacional reducido.
- **Caso G** — audita la equivalencia numérica pandas/Spark.
- **Caso F** — versiona el subset en lakeFS para reproducibilidad.
