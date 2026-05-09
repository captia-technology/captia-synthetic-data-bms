# Isolation Forest

Isolation Forest es un algoritmo de detección de anomalías no supervisado
basado en árboles aleatorios. Idea clave: las anomalías se aíslan con
menos cortes que las observaciones normales, porque viven en regiones de
baja densidad del espacio.

Hiperparámetros:

- `n_estimators` (≈100) — número de árboles.
- `contamination` — proporción esperada de anomalías (0.01–0.1 típico).
- `max_samples` — muestras por árbol (256 estándar).

Devuelve un score por punto. Un score < 0 (isolation depth corta) marca
anomalía; > 0 marca normal. Bueno para datasets HVAC con desbalance
extremo.

Limitaciones:

- No explica *por qué* es anómalo — combinar con SHAP.
- Sensible a cardinalidad baja (categóricas no codificadas).
- Asume features numéricos.
