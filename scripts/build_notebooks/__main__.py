"""Punto de entrada del generador de notebooks didácticos."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_notebooks import (  # noqa: E402
    case_a,
    case_b,
    case_c,
    case_d,
    case_e,
    case_f,
    case_g,
    case_h,
    case_i,
    case_j,
    case_overview,
)


def main() -> None:
    target = ROOT / "notebooks"
    total = 0
    for module in (
        case_overview,
        case_a,
        case_b,
        case_c,
        case_d,
        case_e,
        case_f,
        case_g,
        case_h,
        case_i,
        case_j,
    ):
        n = module.build(target)
        print(f"  {module.__name__:55s}  -> {n} notebooks")
        total += n
    print(f"\nGenerated {total} notebooks under {target.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
