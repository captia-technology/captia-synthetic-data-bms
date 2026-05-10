"""Builder reutilizable para los 42 notebooks didácticos del repo.

Diseño:

- Cada notebook se define como una lista de tuplas ``(kind, content)``
  donde ``kind`` es ``"md"`` o ``"py"`` y ``content`` es una cadena.
- El builder escribe nbformat 4 con kernelspec Python 3.12.
- Re-ejecuciones son idempotentes (no se cambia metadata extra).

Uso (importable):

    from scripts._nb_builder import write_notebook

    write_notebook(
        path=Path("notebooks/00_project_overview/00_demo.ipynb"),
        title="Demo",
        cells=[("md", "# Hola"), ("py", "print('hi')")]
    )
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

NB_FORMAT = 4
NB_FORMAT_MINOR = 5

KERNEL = {
    "display_name": "Python 3.12",
    "language": "python",
    "name": "python3",
}

LANGUAGE_INFO = {
    "codemirror_mode": {"name": "ipython", "version": 3},
    "file_extension": ".py",
    "mimetype": "text/x-python",
    "name": "python",
    "nbconvert_exporter": "python",
    "pygments_lexer": "ipython3",
    "version": "3.12",
}


def _split_lines(text: str) -> list[str]:
    """Devuelve la fuente como lista de líneas con ``\n`` salvo la última."""
    if not text:
        return [""]
    lines = text.splitlines(keepends=True)
    return lines


def _cell_id(source: str, idx: int) -> str:
    """ID determinista, alfanumérico, 8 caracteres."""
    h = hashlib.sha256(f"{idx}-{source[:200]}".encode()).hexdigest()[:8]
    return f"c{h}"


def make_md_cell(source: str, *, idx: int) -> dict:
    return {
        "cell_type": "markdown",
        "id": _cell_id(source, idx),
        "metadata": {},
        "source": _split_lines(source),
    }


def make_code_cell(source: str, *, idx: int) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": _cell_id(source, idx),
        "metadata": {},
        "outputs": [],
        "source": _split_lines(source),
    }


def write_notebook(
    *,
    path: Path,
    title: str,
    cells: Iterable[tuple[str, str]],
) -> None:
    """Construye y escribe un .ipynb en ``path``.

    El primer elemento de ``cells`` debería ser markdown con el título y
    metadata canónica del notebook (caso, capa, spec).
    """
    cell_list: list[dict] = []
    for idx, (kind, content) in enumerate(cells):
        if kind == "md":
            cell_list.append(make_md_cell(content, idx=idx))
        elif kind == "py":
            cell_list.append(make_code_cell(content, idx=idx))
        else:
            raise ValueError(f"Unknown cell kind: {kind!r}")

    notebook = {
        "cells": cell_list,
        "metadata": {
            "kernelspec": KERNEL,
            "language_info": LANGUAGE_INFO,
            "captia": {"title": title, "schema": "captia_point_v1", "seed": 42},
        },
        "nbformat": NB_FORMAT,
        "nbformat_minor": NB_FORMAT_MINOR,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(notebook, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def header(*, kind: str, title: str, case: str, layer: str, spec: str) -> str:
    """Devuelve el bloque markdown de cabecera con metadata trazable."""
    return (
        f"# {title}\n\n"
        f"> _{kind} · Caso de uso: **{case}** · Capa Medallion: **{layer}** · Spec: `{spec}`_\n\n"
        "Material docente del proyecto **CAPTIA Synthetic Data BMS** — IES Dr. Lluís Simarro,\n"
        "Curso de Especialización IA & Big Data 2025-2026.\n"
    )


SETUP_BLOCK = """\
# Setup canónico — todos los notebooks didácticos lo usan
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path.cwd()
while ROOT.name and not (ROOT / "pyproject.toml").exists():
    ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from notebooks._common.captia_schema import (
    CANONICAL_TAGS, MEASUREMENT_TELEMETRY, MEASUREMENT_FAULT_LABELS,
    DEFAULT_BUCKET_RETENTIONS, KNOWN_VARIABLES,
    build_topic, build_line_protocol, validate_canonical_tags,
)
from notebooks._common.connection import load_env, get_influx_client, get_default_bucket
from notebooks._common.plotting import setup_default_style, plot_timeseries, plot_distribution
import notebooks._common.synthetic_mocks as mocks

SEED = 42
rng = np.random.default_rng(SEED)
setup_default_style()
load_env()
print(f"ROOT={ROOT}, SEED={SEED}, default_bucket={get_default_bucket()}")
"""
