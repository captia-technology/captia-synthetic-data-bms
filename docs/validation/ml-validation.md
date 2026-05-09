# Validación de modelos ML

> **Última verificación:** 2026-05-10
> **Casos:** B (forecast consumo), C (anomalías HVAC), D (ocupación), E
> (predicción solar).

## Principios

1. **Split temporal, no aleatorio** — `TimeSeriesSplit` o índices
   ordenados.
2. **Métricas robustas al desbalance** (F1 macro, balanced accuracy).
3. **Naive como baseline obligatoria** — superarla es requisito mínimo.
4. **Walk-forward** para validación a largo plazo.
5. **Sin leakage** — las features se calculan solo con datos pasados
   (`shift(1)` antes de `rolling`).

## Métricas por caso

| Caso | Métrica primaria | Baseline mínima |
|---|---|---|
| B (forecast 24h) | MAE (kW) | naive 24 h atrás |
| C (anomalías HVAC) | AUC ROC + recall por tipo | constante 50 % |
| D (ocupación) | F1 binario | LogisticRegression |
| E (solar) | RMSE (W/m²) | persistencia |
| J (congestión) | balanced_accuracy | clase mayoritaria |

## Walk-forward

Usado en Caso B notebook 05:

```python
def walk_forward_split(idx, train_weeks=8, step_hours=24, n_folds=8):
    folds = []
    cur = train_weeks * 7 * 24
    while cur + step_hours < len(idx) and len(folds) < n_folds:
        folds.append((idx[:cur], idx[cur:cur + step_hours]))
        cur += step_hours
    return folds
```

## Drift detection

Implementado vía KL divergence en `notebooks/07_*/03_reglas_calidad_oro_ml.ipynb`.
Umbral típico: KL < 1.0 considerado estable. > 2.0 dispara alerta.

## Re-entrenamiento

Política recomendada (no aplicada automáticamente en v1):

- **Caso B**: re-entrenar cada semana (Sunday 03:00 UTC).
- **Caso C**: re-entrenar mensualmente.
- **Caso D**: re-entrenar por trimestre.
- **Caso E**: re-entrenar tras descargar nuevo lote ERA5.

## Reproducibilidad

Cada modelo lleva:

- `random_state=42` o equivalente.
- `mlflow.set_tag("lakefs_tag", "case_X/dataset_v1")`.
- Hash SHA-256 del fichero parquet de features.

## Errores comunes

1. **Random split** — `shuffle=False` siempre en TS.
2. **MAPE con valores 0** — usar MAE o sMAPE.
3. **Predicción negativa** sin clip (consumo, irradiancia).
4. **Comparar accuracy entre datasets desbalanceados** — usar
   balanced_accuracy.
