"""Auditoría de trazabilidad spec ↔ test (H-12).

Verifica que todas las rutas de archivo de test referenciadas en
``docs/audit/SPEC_TEST_TRACEABILITY.md`` existen en el repo. Esto evita
que la matriz de trazabilidad rote (link-rot) cuando alguien renombra
o mueve un archivo de test sin actualizar la matriz.

Cierra el hallazgo H-12 (`AUDIT_REPORT.md` — physics specs ortogonales
a tests).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX = REPO_ROOT / "docs" / "audit" / "SPEC_TEST_TRACEABILITY.md"

# Patrones aceptables: rutas relativas al repo terminadas en .py.
_TEST_PATH_RE = re.compile(
    r"`(tests/integration/[A-Za-z0-9_/.-]+\.py|"
    r"extensions/bms_calibration/tests/[A-Za-z0-9_/.-]+\.py|"
    r"modules/bms-data-generator/tests/[A-Za-z0-9_/.-]+\.py)"
)


def _extract_test_paths(text: str) -> set[str]:
    """Extrae rutas de archivos de test de la matriz (sin ::node_id)."""
    paths: set[str] = set()
    for match in _TEST_PATH_RE.finditer(text):
        path_str = match.group(1)
        # Strip ::node_id si está presente.
        if "::" in path_str:
            path_str = path_str.split("::", 1)[0]
        paths.add(path_str)
    return paths


@pytest.mark.integration
def test_traceability_matrix_exists() -> None:
    """La matriz misma existe."""
    assert MATRIX.exists(), f"Falta {MATRIX}"


@pytest.mark.integration
def test_all_referenced_test_files_exist() -> None:
    """Todo archivo `tests/...py` citado en la matriz existe en el repo."""
    text = MATRIX.read_text(encoding="utf-8")
    paths = _extract_test_paths(text)
    assert paths, "No se encontró ninguna ruta de test en la matriz — regex roto"

    missing: list[str] = []
    for rel_path in sorted(paths):
        full = REPO_ROOT / rel_path
        if not full.exists():
            missing.append(rel_path)

    assert not missing, (
        f"{len(missing)} archivos de test referenciados en SPEC_TEST_TRACEABILITY.md "
        f"no existen:\n  - " + "\n  - ".join(missing)
    )


@pytest.mark.integration
def test_critical_recent_patches_are_traced() -> None:
    """Los patches recientes (002-008) tienen entrada en la matriz."""
    text = MATRIX.read_text(encoding="utf-8")
    for patch_id in ("002", "003", "004", "005", "007", "008"):
        assert f"| {patch_id} |" in text, (
            f"PATCH {patch_id} no aparece en la matriz de trazabilidad"
        )


@pytest.mark.integration
def test_canonical_schema_rule_is_traced() -> None:
    """R-INF-01 (schema canónico) debe estar trazada — es la regla más crítica."""
    text = MATRIX.read_text(encoding="utf-8")
    assert "R-INF-01" in text
    # Y debe enlazar a al menos uno de los tests de telegraf.
    assert (
        "test_telegraf_canonical_schema.py" in text
        or "test_telegraf_routing_audit.py" in text
    ), "R-INF-01 sin test trazable a telegraf"
