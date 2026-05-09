# Caso F — MLOps y ciclo de vida de modelos

> **Última verificación:** 2026-05-10
> **Audiencia:** equipo G4 (transversal).
> **Capa Medallion primaria:** transversal.
> **Notebooks:** 3 (`notebooks/06_case_F_mlops/`).

## Objetivo

Definir e implementar la infraestructura MLOps del proyecto: tracking de
experimentos con MLflow, versionado de datasets con lakeFS y convención de
nomenclatura para garantizar reproducibilidad.

> **Nota v1:** este repo no levanta servidor MLflow ni lakeFS en
> `make demo`. Los notebooks usan **MLflow local con SQLite** y simulan
> tags lakeFS con hashes locales. Ver
> [`docs/operations/environment.md`](../operations/environment.md) para
> opciones de despliegue completo.

## Datos esperados

Sin dataset propio. Caso F actúa sobre los artefactos de los demás casos
(B/C/D/E/H/J).

## Capas Medallion

Caso F es **transversal**: orquesta versionado y trazabilidad sin pertenecer
a una capa concreta.

## Notebooks asociados

1. `01_mlflow_lakefs_overview.ipynb` — conceptos: experiment, run, tag.
2. `02_tracking_experimentos.ipynb` — run completo del baseline Caso B con
   métricas, params y artefactos.
3. `03_reproducibilidad_datasets_modelos.ipynb` — hash dataset, hash modelo,
   verificación bit-a-bit.

## Convención de nomenclatura

```
experiment-name = case_<X>_<modelo>_<año>
run-name        = <modelo_corto>_<seed>_<n>
artifact-tag    = case_<X>/<entregable>_v<n>
lakefs-tag      = case_<X>/<dataset>_v<n>
```

Ejemplo:

- `experiment_name = case_B_baseline_2026`
- `run_name = rf_v1_seed42`
- `lakefs_tag = case_B/baseline_v1`

## Validación

- Reproducibilidad estricta del dataset (hash SHA-256 idéntico entre runs).
- Reproducibilidad aproximada del modelo (joblib lleva metadata de hora;
  comparar pickle puro o usar `joblib.dump(..., compress=0)` y stripping).
- Cada run referencia su `lakefs_tag`.

## Errores comunes

1. **Cambiar hiperparámetros sin nuevo run** — pierdes la traza.
2. **Subir artefactos enormes** (CSVs) en lugar de versionar el dataset.
3. **No registrar el `seed`** — la reproducibilidad se rompe.
4. **MLflow tracking URI por defecto** — los runs van a `/tmp` y se pierden.

## Reutilización con datos reales

El stack MLflow + lakeFS escala a producción sin cambios en los notebooks.
Solo se actualiza:

- `MLFLOW_TRACKING_URI=https://mlflow.iti.es`
- `LAKEFS_ENDPOINT=https://lakefs.iti.es`

## Coordinación con otros casos

- **Caso B/C/D/E/H/J** — todos registran sus experimentos siguiendo la
  convención del Caso F.
- **Caso G** — audita el contenido de `mlruns/` y verifica que cada run
  tiene baseline documentada y referencia lakeFS.
