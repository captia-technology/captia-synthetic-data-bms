"""Genera los CSV mock deterministas para los notebooks didácticos.

Usar:

    uv run python scripts/build_notebook_data.py

Re-ejecuciones producen ficheros idénticos (seed=42).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Hacer accesible el paquete `notebooks._common` desde la raíz del repo
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from notebooks._common.synthetic_mocks import (  # noqa: E402
    make_bdg2_education_subset,
    make_chatbot_golden_set,
    make_era5_xativa_mock,
    make_ingauge_aula01_mock,
    make_lbnl_fdd_rtu_mock,
    make_traffic_camera_mock,
)

OUT = ROOT / "notebooks" / "_data"
OUT.mkdir(parents=True, exist_ok=True)


def _save(df, name: str, header_note: str) -> None:
    target = OUT / name
    note = f"# MOCK — {header_note}\n"
    csv_text = df.to_csv(index=False)
    target.write_text(note + csv_text, encoding="utf-8")
    print(f"wrote {target.relative_to(ROOT)} ({len(df)} rows)")


def main() -> None:
    df_ingauge, _ = make_ingauge_aula01_mock()
    _save(df_ingauge, "ingauge_aula01_mock.csv", "sintético In-Gauge AULA01 (1 semana × 1min)")

    df_bdg2, _ = make_bdg2_education_subset()
    _save(df_bdg2, "bdg2_education_subset_mock.csv", "sintético BDG2 educacional (6 edif × 12m horarios)")

    df_lbnl, _ = make_lbnl_fdd_rtu_mock()
    _save(df_lbnl, "lbnl_fdd_rtu_mock.csv", "sintético LBNL FDD RTU (14 días × 1min con 4 fallos)")

    df_era5, _ = make_era5_xativa_mock()
    _save(df_era5, "era5_xativa_mock.csv", "sintético ERA5 Xàtiva (30 días horarios)")

    df_traffic, _ = make_traffic_camera_mock()
    _save(df_traffic, "traffic_camera_mock.csv", "sintético DGT cameras (7 días × 15min)")

    df_golden = make_chatbot_golden_set()
    _save(df_golden, "chatbot_golden_set.csv", "golden set chatbot Caso H (40 preguntas)")


if __name__ == "__main__":
    main()
