"""Helpers compartidos por los módulos de cada caso."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from scripts._nb_builder import SETUP_BLOCK, header, write_notebook


def emit(
    *,
    target: Path,
    rel_path: str,
    title: str,
    case: str,
    layer: str,
    spec: str,
    sections: list[tuple[str, str]],
    kind: str = "Tutorial",
) -> Path:
    """Escribe un notebook didáctico de las 18 secciones canónicas.

    Parameters
    ----------
    target:
        Raíz ``notebooks/``.
    rel_path:
        Ruta relativa, p.ej. ``02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb``.
    sections:
        Lista de 18 tuplas ``(markdown_section, optional_python_block)``.
        El markdown ya contiene el título "## N. ...". El bloque python puede
        ser ``""`` para secciones que solo son markdown.
    """
    full_path = target / rel_path
    cells: list[tuple[str, str]] = [
        ("md", header(kind=kind, title=title, case=case, layer=layer, spec=spec))
    ]
    for md, code in sections:
        cells.append(("md", md))
        if code.strip():
            cells.append(("py", code))
    write_notebook(path=full_path, title=title, cells=cells)
    return full_path


def section(
    n: int,
    name: str,
    body_md: str,
    code: str = "",
) -> tuple[str, str]:
    """Construye una tupla ``(markdown, code)`` con el encabezado canónico."""
    md = f"## {n}. {name}\n\n{body_md.strip()}\n"
    return md, code


def setup_section(extra_md: str = "") -> tuple[str, str]:
    """Sección 8 con el setup canónico común."""
    body = (
        "Cargamos las variables de entorno (`.env`), inicializamos `numpy` con "
        "`seed=42` y aplicamos el estilo de plotting compartido. Los helpers "
        "viven en `notebooks/_common/`.\n"
    )
    if extra_md:
        body = body + "\n" + extra_md.strip() + "\n"
    return section(8, "Setup y variables de entorno", body, SETUP_BLOCK)


def common_summary(
    *,
    next_notebook: str | None = None,
    docs_link: str | None = None,
    extra_bullets: Iterable[str] = (),
) -> tuple[str, str]:
    """Sección 18 estándar con enlaces."""
    bullets = []
    if next_notebook:
        bullets.append(f"- Siguiente notebook: `{next_notebook}`.")
    if docs_link:
        bullets.append(f"- Documento web del caso: `{docs_link}`.")
    bullets.extend(f"- {b}" for b in extra_bullets)
    bullets_md = "\n".join(bullets) if bullets else ""
    body = (
        "Recuerda los conceptos principales del notebook y enlaza al siguiente paso.\n\n"
        + bullets_md
    )
    return section(18, "Resumen final y próximos pasos", body)
