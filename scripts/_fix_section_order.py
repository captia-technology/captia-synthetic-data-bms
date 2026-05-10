"""Reordena las llamadas dentro de cada `sections = [...]`:

mueve `setup_section()` antes que `section(8, "Schema CAPTIA esperado", ...)`.

Pasada una vez para corregir la herencia de la primera versión del builder
donde el setup quedaba detrás del schema.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = ROOT / "scripts" / "build_notebooks"


def fix_file(path: Path) -> int:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    src_lines = src.splitlines(keepends=True)
    edits: list[tuple[int, int, str]] = []  # (start_line, end_line, replacement)

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and getattr(node, "targets", None)):
            continue
        target_names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "sections" not in target_names:
            continue
        if not isinstance(node.value, ast.List):
            continue

        # Identificar cada elemento por su rango de líneas
        elements = node.value.elts
        if not elements:
            continue
        # Encontrar índices de setup_section() y de section(8, "Schema CAPTIA esperado", ...)
        setup_idx = None
        schema_idx = None
        for i, el in enumerate(elements):
            label = _classify_element(el)
            if label == "setup":
                setup_idx = i
            elif label == "schema":
                schema_idx = i
        if setup_idx is None or schema_idx is None:
            continue
        if setup_idx <= schema_idx:
            continue  # ya está bien ordenado

        # Obtener los rangos de líneas de los elementos
        ranges = [(_first_line(el), _last_line(el)) for el in elements]
        # Reordenar: mover el elemento `setup_idx` justo antes de `schema_idx`.
        new_order = list(range(len(elements)))
        item = new_order.pop(setup_idx)
        # Insertar en la nueva posición; dado que pop se hizo desde un índice mayor,
        # el destino schema_idx no se ha desplazado.
        new_order.insert(schema_idx, item)

        # Capturar el texto fuente de cada elemento (incluyendo trailing comma + newline)
        elem_texts: list[str] = []

        # Texto de cada elemento sin trailing comma:
        for el, (s, e) in zip(elements, ranges, strict=True):
            chunk = _slice_lines(src_lines, s, e, el.col_offset, el.end_col_offset)
            elem_texts.append(chunk)

        # Construir nuevo cuerpo: indentación = misma que el primer elemento
        # Tomamos el indent de la primera linea del primer elemento
        first_el_indent = _line_indent(src_lines[elements[0].lineno - 1])
        sep = ",\n" + first_el_indent

        new_body_inner = sep.join(elem_texts[i] for i in new_order) + ","
        # Reescribir desde la primera linea del primer elemento hasta la última del último.
        body_first = elements[0].lineno
        body_last = elements[-1].end_lineno
        # Replacement preserva contexto de líneas: ponemos new_body_inner desde el indent.
        replacement = first_el_indent + new_body_inner + "\n"
        edits.append((body_first, body_last, replacement))

    if not edits:
        return 0
    # Aplicar edits de abajo a arriba
    edits.sort(key=lambda e: e[0], reverse=True)
    out_lines = list(src_lines)
    for start_line, end_line, replacement in edits:
        del out_lines[start_line - 1 : end_line]
        out_lines.insert(start_line - 1, replacement)
    new_src = "".join(out_lines)
    if new_src != src:
        path.write_text(new_src, encoding="utf-8")
        return len(edits)
    return 0


def _classify_element(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name):
            if f.id == "setup_section":
                return "setup"
            if f.id == "section" and node.args:
                # primer arg número, segundo arg = "Schema CAPTIA esperado"
                if len(node.args) >= 2:
                    a0, a1 = node.args[0], node.args[1]
                    if (
                        isinstance(a0, ast.Constant)
                        and a0.value == 8
                        and isinstance(a1, ast.Constant)
                        and a1.value == "Schema CAPTIA esperado"
                    ):
                        return "schema"
    return None


def _first_line(node: ast.AST) -> int:
    return node.lineno


def _last_line(node: ast.AST) -> int:
    return node.end_lineno


def _slice_lines(
    lines: list[str], start_line: int, end_line: int, col_off: int, end_col_off: int
) -> str:
    if start_line == end_line:
        return lines[start_line - 1][col_off:end_col_off]
    parts = [lines[start_line - 1][col_off:]]
    for ln in range(start_line, end_line - 1):
        parts.append(lines[ln])
    parts.append(lines[end_line - 1][:end_col_off])
    return "".join(parts)


def _line_indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" "))]


def main() -> int:
    total = 0
    for f in sorted(TARGET_DIR.glob("case_*.py")):
        n = fix_file(f)
        if n:
            print(f"  {f.name}: {n} bloques reordenados")
        total += n
    print(f"\nTotal: {total} bloques fix")
    # Verificar parsing tras edits
    for f in sorted(TARGET_DIR.glob("case_*.py")):
        try:
            ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            print(f"  SYNTAX ERROR in {f.name}: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
