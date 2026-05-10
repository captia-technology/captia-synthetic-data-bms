"""Helpers de evaluación rigurosa para los notebooks de modelado.

Diseño:

- **Validación temporal** (`TimeSeriesSplit` wrappers).
- **Intervalos de confianza bootstrap** (95 %).
- **Baselines reutilizables** (persistencia, naïve-24h, climatología, regla
  física, threshold).
- **Métricas con IC**.

Estos helpers atacan directamente los hallazgos NA-01 (sin baseline) y
NA-02 (sin CV temporal) de la auditoría
``docs/audit/NOTEBOOK_AUDIT.md``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from notebooks._common.captia_schema import DEFAULT_SEED

# ---------------------------------------------------------------------------
# Métricas + bootstrap.
# ---------------------------------------------------------------------------


def mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true, y_pred) -> float:
    err = np.asarray(y_true) - np.asarray(y_pred)
    return float(np.sqrt(np.mean(err**2)))


def smape(y_true, y_pred) -> float:
    """sMAPE — robusto a y=0 (a diferencia de MAPE)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    denom = np.where(denom < 1e-9, 1e-9, denom)
    return float(100 * np.mean(np.abs(y_true - y_pred) / denom))


def bootstrap_ci(
    y_true,
    y_pred,
    metric: Callable[[Any, Any], float],
    *,
    n_iter: int = 1000,
    alpha: float = 0.05,
    seed: int = DEFAULT_SEED,
) -> tuple[float, float, float]:
    """Devuelve ``(point_estimate, lo, hi)`` con IC al ``1-alpha``."""
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n = len(y_true)
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    samples = []
    for _ in range(n_iter):
        idx = rng.integers(0, n, size=n)
        samples.append(metric(y_true[idx], y_pred[idx]))
    point = metric(y_true, y_pred)
    lo, hi = np.quantile(samples, [alpha / 2, 1 - alpha / 2])
    return float(point), float(lo), float(hi)


# ---------------------------------------------------------------------------
# Baselines de regresión.
# ---------------------------------------------------------------------------


def naive_persistence_24h(y_train: pd.Series, y_test: pd.Series) -> np.ndarray:
    """Baseline: el valor de hoy a la hora h = el valor de ayer a la misma hora."""
    full = pd.concat([y_train, y_test])
    pred_full = full.shift(24)
    return pred_full.loc[y_test.index].bfill().to_numpy()


def naive_persistence_1h(y_train: pd.Series, y_test: pd.Series) -> np.ndarray:
    """Baseline: el valor en t = valor en t-1."""
    full = pd.concat([y_train, y_test])
    pred_full = full.shift(1)
    return pred_full.loc[y_test.index].bfill().to_numpy()


def climatology_by_hour(y_train: pd.Series, y_test: pd.Series) -> np.ndarray:
    """Baseline: media histórica del valor a esa hora del día."""
    if not isinstance(y_train.index, pd.DatetimeIndex):
        raise ValueError("y_train debe tener DatetimeIndex")
    by_hour = y_train.groupby(y_train.index.hour).mean()
    return y_test.index.hour.map(by_hour).to_numpy()


# ---------------------------------------------------------------------------
# Baseline analítico para Caso D (balance de masa CO₂).
# ---------------------------------------------------------------------------


def occupancy_from_co2_balance(
    co2_series: pd.Series,
    *,
    volume_m3: float = 180.0,
    vent_rate_l_s: float = 12.0,
    co2_outdoor_ppm: float = 420.0,
    gen_l_s_per_person: float = 4.5e-3,
) -> pd.Series:
    """Inversión analítica del balance de masa CO₂.

    Modelo (Wang et al. 2017, ASHRAE 62.1):

    .. math::

        V \\frac{dC}{dt} = G \\cdot N(t) - \\dot V_{vent}(C(t) - C_{out})

    Despejando:

    .. math::

        \\hat N(t) = \\frac{V \\frac{dC}{dt} + \\dot V_{vent}(C - C_{out})}{G}

    Devuelve ocupación estimada (no entera; redondear a posteriori).
    """
    if not isinstance(co2_series.index, pd.DatetimeIndex):
        raise ValueError("co2_series debe tener DatetimeIndex")
    # Convertir L/s a m³/s
    vent_rate_m3_s = vent_rate_l_s * 1e-3
    gen_m3_s = gen_l_s_per_person * 1e-3
    # dC/dt en ppm/s: aproximamos por diferencias finitas con paso = índice
    dt_s = co2_series.index.to_series().diff().dt.total_seconds().bfill()
    dc_dt = co2_series.diff().bfill() / dt_s
    # ppm → fracción (×1e-6)
    dc_dt_frac = dc_dt * 1e-6
    co2_frac = (co2_series - co2_outdoor_ppm) * 1e-6
    n_hat = (volume_m3 * dc_dt_frac + vent_rate_m3_s * co2_frac) / gen_m3_s
    return n_hat.clip(lower=0)


def occupancy_from_co2_threshold(
    co2_series: pd.Series, *, threshold_ppm: float = 600.0
) -> np.ndarray:
    """Baseline trivial: ocupado si CO₂ > umbral."""
    return (co2_series > threshold_ppm).astype(int).to_numpy()


# ---------------------------------------------------------------------------
# Baselines de detección de anomalías (Caso C).
# ---------------------------------------------------------------------------


def hvac_rule_dt_zero(
    df: pd.DataFrame,
    *,
    supply_col: str = "SA_TEMP",
    return_col: str = "RA_TEMP",
    threshold_dt: float = 0.5,
) -> np.ndarray:
    """Regla física: |ΔT| < umbral mientras la unidad debería estar enfriando.

    Devuelve un score continuo: cuanto más bajo el ΔT esperado, más anómalo.
    """
    dt_supply_return = df[return_col] - df[supply_col]
    # Para anomalías de cooling, esperamos dt_supply_return > threshold (return > supply)
    # Un valor < threshold sugiere problema. Convertimos a score: max(0, threshold - dt).
    score = np.maximum(0, threshold_dt - dt_supply_return)
    return score.to_numpy()


def rolling_zscore_anomaly(series: pd.Series, *, window: int = 60) -> np.ndarray:
    """Score |z-score| sobre rolling mean/std."""
    rmean = series.rolling(window=window, min_periods=window // 2).mean()
    rstd = series.rolling(window=window, min_periods=window // 2).std()
    z = (series - rmean) / rstd.replace(0, np.nan)
    return z.fillna(0).abs().to_numpy()


# ---------------------------------------------------------------------------
# CV temporal con métricas + IC bootstrap.
# ---------------------------------------------------------------------------


@dataclass
class FoldResult:
    fold: int
    n_train: int
    n_test: int
    metrics: dict[str, float]


def time_series_cv_evaluate(
    estimator_fn: Callable[[], Any],
    X: pd.DataFrame,
    y: pd.Series,
    *,
    n_splits: int = 5,
    metrics: dict[str, Callable[[Any, Any], float]] | None = None,
    is_classifier: bool = False,
) -> pd.DataFrame:
    """Walk-forward CV temporal.

    Devuelve DataFrame con una fila por fold y columnas por métrica.
    No requiere sklearn-TimeSeriesSplit explícito — usa cortes incrementales.
    """
    from sklearn.model_selection import TimeSeriesSplit

    if metrics is None:
        if is_classifier:
            from sklearn.metrics import f1_score, precision_score, recall_score

            metrics = {
                "precision": lambda y_t, y_p: float(precision_score(y_t, y_p, zero_division=0)),
                "recall": lambda y_t, y_p: float(recall_score(y_t, y_p, zero_division=0)),
                "f1": lambda y_t, y_p: float(f1_score(y_t, y_p, zero_division=0)),
            }
        else:
            metrics = {"MAE": mae, "RMSE": rmse, "sMAPE": smape}

    tscv = TimeSeriesSplit(n_splits=n_splits)
    rows = []
    for fold, (idx_tr, idx_te) in enumerate(tscv.split(X)):
        X_tr, X_te = X.iloc[idx_tr], X.iloc[idx_te]
        y_tr, y_te = y.iloc[idx_tr], y.iloc[idx_te]
        if y_tr.nunique() < 2 and is_classifier:
            # Sin ambas clases, el modelo no puede aprender — fold inválido
            continue
        est = estimator_fn()
        est.fit(X_tr, y_tr)
        y_pred = est.predict(X_te)
        row: dict[str, Any] = {"fold": fold, "n_train": len(X_tr), "n_test": len(X_te)}
        for name, fn in metrics.items():
            row[name] = fn(y_te.to_numpy(), y_pred)
        rows.append(row)
    return pd.DataFrame(rows)


def summarise_cv(results: pd.DataFrame, metric: str) -> dict[str, float]:
    """Resumen mean/std/IC95% de la métrica indicada sobre folds."""
    if results.empty:
        return {"mean": float("nan"), "std": float("nan"), "lo": float("nan"), "hi": float("nan")}
    vals = results[metric].to_numpy()
    return {
        "mean": float(np.mean(vals)),
        "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
        "lo": float(np.quantile(vals, 0.025)),
        "hi": float(np.quantile(vals, 0.975)),
    }


# ---------------------------------------------------------------------------
# Tabla comparativa de modelos.
# ---------------------------------------------------------------------------


def compare_models(
    y_true,
    predictions: dict[str, Any],
    *,
    is_classifier: bool = False,
) -> pd.DataFrame:
    """DataFrame con métricas + IC bootstrap por modelo.

    ``predictions`` es ``{nombre: y_pred}``.
    """
    if is_classifier:
        from sklearn.metrics import f1_score, precision_score, recall_score

        metrics = {
            "precision": lambda yt, yp: float(precision_score(yt, yp, zero_division=0)),
            "recall": lambda yt, yp: float(recall_score(yt, yp, zero_division=0)),
            "f1": lambda yt, yp: float(f1_score(yt, yp, zero_division=0)),
        }
    else:
        metrics = {"MAE": mae, "RMSE": rmse, "sMAPE": smape}

    rows = []
    for name, y_pred in predictions.items():
        row: dict[str, Any] = {"model": name}
        for m_name, m_fn in metrics.items():
            point, lo, hi = bootstrap_ci(y_true, y_pred, m_fn, n_iter=300)
            row[m_name] = round(point, 3)
            row[f"{m_name}_lo"] = round(lo, 3)
            row[f"{m_name}_hi"] = round(hi, 3)
        rows.append(row)
    return pd.DataFrame(rows).set_index("model")
