"""Helpers de visualización compartidos entre notebooks didácticos.

Nota: ``matplotlib`` se importa de forma perezosa dentro de cada función
para que ``notebooks._common.plotting`` se pueda importar en entornos sin
matplotlib (por ejemplo, smoke tests o CI sin dependencias visuales).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

CAPTIA_PALETTE = ["#3F51B5", "#FF5722", "#4CAF50", "#9C27B0", "#00BCD4", "#FFC107"]


def setup_default_style() -> None:
    """Aplica un estilo coherente para todos los notebooks."""
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.figsize": (10, 4),
            "axes.grid": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.alpha": 0.25,
            "axes.titleweight": "bold",
            "axes.labelweight": "bold",
        }
    )


def plot_timeseries(
    df: pd.DataFrame,
    *,
    time_col: str = "timestamp",
    value_cols: list[str] | None = None,
    title: str = "Serie temporal",
    ax: Any | None = None,
) -> Any:
    """Dibuja una o varias columnas contra ``time_col``."""
    import matplotlib.pyplot as plt

    if value_cols is None:
        value_cols = [c for c in df.columns if c != time_col][:3]
    if ax is None:
        _, ax = plt.subplots()
    for i, col in enumerate(value_cols):
        ax.plot(
            df[time_col],
            df[col],
            color=CAPTIA_PALETTE[i % len(CAPTIA_PALETTE)],
            label=col,
            linewidth=1.0,
        )
    ax.set_title(title)
    ax.set_xlabel(time_col)
    ax.legend(loc="upper right", fontsize=8)
    return ax


def plot_distribution(
    df: pd.DataFrame,
    *,
    column: str,
    by: str | None = None,
    bins: int = 30,
    title: str | None = None,
) -> Any:
    """Histograma simple, opcionalmente por categoría ``by``."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    if by is None:
        ax.hist(df[column].dropna(), bins=bins, color=CAPTIA_PALETTE[0], edgecolor="white")
    else:
        for i, (key, group) in enumerate(df.groupby(by)):
            ax.hist(
                group[column].dropna(),
                bins=bins,
                alpha=0.55,
                label=str(key),
                color=CAPTIA_PALETTE[i % len(CAPTIA_PALETTE)],
                edgecolor="white",
            )
        ax.legend(title=by)
    ax.set_title(title or f"Distribución de {column}")
    ax.set_xlabel(column)
    ax.set_ylabel("frecuencia")
    return ax
