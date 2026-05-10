"""Visualizaciones diagnósticas estándar para notebooks de modelado.

Atacan el hallazgo NA-07 (visualizaciones decorativas) de la auditoría:

- ``plot_regression_diagnostic`` → 4-panel (timeline, scatter, residuos, CDF).
- ``plot_classification_diagnostic`` → ROC + PR + matriz confusión + score-by-class.
- ``plot_iot_pipeline_diagnostic`` → timeline publish + lag distribution.

Todas las funciones usan imports perezosos para no requerir matplotlib en
entornos minimalistas.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def plot_regression_diagnostic(
    y_true,
    y_pred,
    *,
    timestamps: Any | None = None,
    title: str = "Diagnóstico regresión",
    sample_window: int = 168,
):
    """4 paneles: timeline · scatter pred-real · residuos vs índice · CDF errores."""
    import matplotlib.pyplot as plt

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    err = y_true - y_pred

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    ax_tl, ax_sc, ax_res, ax_cdf = axes.flatten()

    # 1. Timeline (1 semana)
    n_show = min(sample_window, len(y_true))
    if timestamps is not None:
        x_show = pd.to_datetime(timestamps)[:n_show]
    else:
        x_show = np.arange(n_show)
    ax_tl.plot(x_show, y_true[:n_show], label="real", color="#3F51B5", linewidth=1.0)
    ax_tl.plot(x_show, y_pred[:n_show], label="predicho", color="#FF5722", linewidth=1.0, alpha=0.9)
    ax_tl.set_title("Timeline (primer fragmento)")
    ax_tl.legend(loc="upper right", fontsize=8)
    ax_tl.tick_params(axis="x", rotation=30)

    # 2. Scatter pred-real con diagonal
    ax_sc.scatter(y_true, y_pred, s=8, alpha=0.4, color="#3F51B5")
    lim = [min(np.min(y_true), np.min(y_pred)), max(np.max(y_true), np.max(y_pred))]
    ax_sc.plot(lim, lim, "--", color="gray", label="y = ŷ")
    # R² simple
    ss_res = np.sum(err**2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    ax_sc.set_title(f"Scatter — R² = {r2:.3f}")
    ax_sc.set_xlabel("real")
    ax_sc.set_ylabel("predicho")
    ax_sc.legend(loc="upper left", fontsize=8)

    # 3. Residuos
    ax_res.scatter(np.arange(len(err)), err, s=4, alpha=0.4, color="#9C27B0")
    ax_res.axhline(0, color="gray", linestyle="--")
    ax_res.set_title(f"Residuos — MAE = {np.mean(np.abs(err)):.3f}")
    ax_res.set_xlabel("índice")

    # 4. CDF de |error|
    abs_err = np.sort(np.abs(err))
    cdf = np.arange(1, len(abs_err) + 1) / len(abs_err)
    ax_cdf.plot(abs_err, cdf, color="#FF5722")
    ax_cdf.set_title("CDF |error|")
    ax_cdf.set_xlabel("|error|")
    ax_cdf.set_ylabel("Pr(|err| ≤ x)")
    ax_cdf.grid(alpha=0.3)

    fig.suptitle(title, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_classification_diagnostic(
    y_true,
    y_score,
    *,
    threshold: float | None = None,
    title: str = "Diagnóstico clasificación",
):
    """ROC + PR + matriz confusión + distribución score por clase."""
    import matplotlib.pyplot as plt
    from sklearn.metrics import (
        ConfusionMatrixDisplay,
        average_precision_score,
        precision_recall_curve,
        roc_auc_score,
        roc_curve,
    )

    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=float)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    ax_roc, ax_pr, ax_cm, ax_dist = axes.flatten()

    # ROC
    fpr, tpr, _ = roc_curve(y_true, y_score)
    auc = roc_auc_score(y_true, y_score)
    ax_roc.plot(fpr, tpr, color="#3F51B5", label=f"ROC AUC={auc:.3f}")
    ax_roc.plot([0, 1], [0, 1], "--", color="gray", alpha=0.6)
    ax_roc.set_title("ROC")
    ax_roc.set_xlabel("FPR")
    ax_roc.set_ylabel("TPR")
    ax_roc.legend(loc="lower right", fontsize=8)
    ax_roc.grid(alpha=0.3)

    # PR
    p, r, _ = precision_recall_curve(y_true, y_score)
    ap = average_precision_score(y_true, y_score)
    ax_pr.plot(r, p, color="#FF5722", label=f"AP={ap:.3f}")
    ax_pr.set_title("Precision-Recall")
    ax_pr.set_xlabel("Recall")
    ax_pr.set_ylabel("Precision")
    ax_pr.legend(loc="lower left", fontsize=8)
    ax_pr.grid(alpha=0.3)

    # Threshold automático: percentil 90 si no se da
    thr = threshold if threshold is not None else float(np.quantile(y_score, 0.9))
    y_pred = (y_score >= thr).astype(int)

    ConfusionMatrixDisplay.from_predictions(y_true, y_pred, ax=ax_cm, cmap="Blues", colorbar=False)
    ax_cm.set_title(f"Confusión @ thr={thr:.3f}")

    # Distribución de score por clase real
    pos = y_score[y_true == 1]
    neg = y_score[y_true == 0]
    ax_dist.hist(neg, bins=30, alpha=0.55, label="y=0", color="#3F51B5", edgecolor="white")
    ax_dist.hist(pos, bins=30, alpha=0.55, label="y=1", color="#FF5722", edgecolor="white")
    ax_dist.axvline(thr, color="black", linestyle="--", label=f"thr={thr:.2f}")
    ax_dist.set_title("Distribución score por clase")
    ax_dist.legend(loc="upper right", fontsize=8)

    fig.suptitle(title, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_iot_pipeline_diagnostic(
    publish_times,
    *,
    title: str = "Pipeline IoT — publicación",
):
    """Timeline + histograma de inter-arrival times."""
    import matplotlib.pyplot as plt

    ts = pd.to_datetime(publish_times).sort_values()
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.5))
    ax_tl, ax_hist = axes

    ax_tl.eventplot(ts.astype("int64").to_numpy() / 1e9, color="#3F51B5", lineoffsets=1)
    ax_tl.set_title("Timeline publicaciones")
    ax_tl.set_xlabel("epoch")
    ax_tl.set_yticks([])

    ia = ts.diff().dt.total_seconds().dropna()
    if len(ia):
        ax_hist.hist(ia, bins=30, color="#FF5722", edgecolor="white")
        ax_hist.set_title(
            f"Inter-arrival times — mediana {ia.median():.3f}s, p99 {ia.quantile(0.99):.3f}s"
        )
        ax_hist.set_xlabel("Δt (s)")

    fig.suptitle(title, fontweight="bold")
    fig.tight_layout()
    return fig
