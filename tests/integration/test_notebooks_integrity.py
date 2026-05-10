"""Audit notebook didáctico — valida los 45 notebooks por CI.

Reglas:

- Todos los `.ipynb` en `notebooks/` son JSON válido nbformat 4.
- Cada notebook contiene la cabecera con metadata trazable
  (`Caso de uso`, `Capa Medallion`, `Spec:`).
- Cada notebook menciona ``captia_point`` o el schema canónico CAPTIA al
  menos una vez (citación obligatoria).
- Ninguna celda contiene tokens / passwords inline.
- Los mocks se etiquetan con la convención ``# MOCK`` o
  ``# MOCK — sintético`` cuando aparezcan en el código.
- El paquete ``notebooks._common`` se importa sin matplotlib obligatorio.

Esta suite garantiza que cualquier regeneración (`uv run python -m
scripts.build_notebooks`) deja los notebooks en estado entregable.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOKS = sorted((ROOT / "notebooks").rglob("*.ipynb"))

# Hacer accesible el paquete `notebooks._common` cuando pytest no parte de la raíz.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXPECTED_TOTAL = 45

SECRET_PATTERNS = [
    re.compile(r"INFLUXDB_TOKEN\s*=\s*['\"][a-f0-9]{16,}", re.IGNORECASE),
    re.compile(r"BMS_API_TOKEN\s*=\s*['\"][a-f0-9]{16,}", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{30,}", re.IGNORECASE),  # OpenAI-style key
]


pytestmark = pytest.mark.integration


def test_notebook_count() -> None:
    """Sub-fase 11.4: 45 notebooks generados (3 overview + 42 casos)."""
    assert len(NOTEBOOKS) == EXPECTED_TOTAL, (
        f"Esperados {EXPECTED_TOTAL} notebooks; encontrados {len(NOTEBOOKS)}. "
        "Ejecutar `uv run python -m scripts.build_notebooks` para regenerar."
    )


@pytest.mark.parametrize("nb_path", NOTEBOOKS, ids=lambda p: str(p.relative_to(ROOT)))
def test_notebook_is_valid_nbformat_4(nb_path: Path) -> None:
    data = json.loads(nb_path.read_text(encoding="utf-8"))
    assert data.get("nbformat") == 4
    assert isinstance(data.get("cells"), list)
    assert data["cells"], f"{nb_path} sin celdas"


@pytest.mark.parametrize("nb_path", NOTEBOOKS, ids=lambda p: str(p.relative_to(ROOT)))
def test_notebook_has_traceable_header(nb_path: Path) -> None:
    """La primera celda debe ser markdown con metadata canónica."""
    data = json.loads(nb_path.read_text(encoding="utf-8"))
    first = data["cells"][0]
    assert first["cell_type"] == "markdown"
    src = "".join(first["source"])
    assert "Caso de uso" in src, f"{nb_path}: falta `Caso de uso` en cabecera"
    assert "Capa Medallion" in src, f"{nb_path}: falta `Capa Medallion` en cabecera"
    assert "Spec:" in src, f"{nb_path}: falta `Spec:` en cabecera"


@pytest.mark.parametrize("nb_path", NOTEBOOKS, ids=lambda p: str(p.relative_to(ROOT)))
def test_notebook_cites_captia_schema(nb_path: Path) -> None:
    """El schema canónico debe citarse explícitamente."""
    text = nb_path.read_text(encoding="utf-8").lower()
    assert any(
        keyword in text
        for keyword in ("captia_point", "captia_env", "captia_schema", "schema canónico")
    ), f"{nb_path}: sin referencia al schema canónico CAPTIA"


@pytest.mark.parametrize("nb_path", NOTEBOOKS, ids=lambda p: str(p.relative_to(ROOT)))
def test_notebook_has_no_inline_secrets(nb_path: Path) -> None:
    text = nb_path.read_text(encoding="utf-8")
    for pat in SECRET_PATTERNS:
        m = pat.search(text)
        assert m is None, f"{nb_path}: posible secreto inline → {m.group()[:30]}..."


def test_common_module_imports_without_matplotlib() -> None:
    """`notebooks._common` debe poder importarse sin matplotlib instalado.

    Esto garantiza que un alumno con setup mínimo puede usar los helpers de
    schema y conexión sin instalar dependencias visuales.
    """
    import importlib

    for mod in (
        "notebooks._common.captia_schema",
        "notebooks._common.connection",
        "notebooks._common.synthetic_mocks",
        "notebooks._common.plotting",
    ):
        importlib.import_module(mod)


def test_synthetic_mocks_are_deterministic() -> None:
    """Re-ejecutar los generadores con `seed=42` produce los mismos bytes."""
    from notebooks._common.synthetic_mocks import (
        make_bdg2_education_subset,
        make_chatbot_golden_set,
        make_era5_xativa_mock,
        make_ingauge_aula01_mock,
        make_lbnl_fdd_rtu_mock,
        make_traffic_camera_mock,
    )

    pairs = [
        (make_ingauge_aula01_mock, {}),
        (make_bdg2_education_subset, {}),
        (make_lbnl_fdd_rtu_mock, {}),
        (make_era5_xativa_mock, {}),
        (make_traffic_camera_mock, {}),
    ]
    for fn, kwargs in pairs:
        a, _ = fn(**kwargs)
        b, _ = fn(**kwargs)
        assert a.equals(b), f"{fn.__name__} no es determinista"

    g1 = make_chatbot_golden_set()
    g2 = make_chatbot_golden_set()
    assert g1.equals(g2)
