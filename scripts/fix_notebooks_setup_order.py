"""Fix notebooks where the setup cell (with `from notebooks._common.*` imports)
appears AFTER cells that already use those imports.

The notebook builder placed the setup at section 8, but sections 7 and earlier
sometimes reference MEASUREMENT_TELEMETRY, CANONICAL_TAGS, build_line_protocol,
etc. We move the setup cell to position 1 (just after the title markdown) so
it runs first.

Usage:
    uv run python scripts/fix_notebooks_setup_order.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import nbformat

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"

# Marker that identifies the setup cell.
SETUP_MARKER = "from notebooks._common.captia_schema import"


def fix_notebook(path: Path) -> bool:
    nb = nbformat.read(path, as_version=4)
    cells = nb.cells
    setup_idx = None
    for i, c in enumerate(cells):
        if c.cell_type == "code" and SETUP_MARKER in c.source:
            setup_idx = i
            break
    if setup_idx is None:
        return False
    # If setup is already at position 0 or 1, we still want it before any other
    # code cell. Find the first code cell index.
    first_code_idx = next((i for i, c in enumerate(cells) if c.cell_type == "code"), None)
    if first_code_idx is None or setup_idx == first_code_idx:
        return False
    # Move setup before first code cell.
    setup_cell = cells.pop(setup_idx)
    cells.insert(first_code_idx, setup_cell)
    nb.cells = cells
    nbformat.write(nb, path)
    return True


def main() -> int:
    notebooks = sorted(
        nb for nb in NOTEBOOKS_DIR.rglob("*.ipynb") if ".ipynb_checkpoints" not in nb.parts
    )
    fixed = 0
    skipped = 0
    for nb in notebooks:
        rel = nb.relative_to(REPO_ROOT)
        try:
            if fix_notebook(nb):
                print(f"FIXED   {rel}")
                fixed += 1
            else:
                skipped += 1
        except Exception as exc:
            print(f"ERROR   {rel}: {exc}", file=sys.stderr)
    print(f"\nFixed {fixed} notebooks, skipped {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
