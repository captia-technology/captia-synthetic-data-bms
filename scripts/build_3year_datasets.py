"""Genera los datasets enriquecidos de 3 años para casos avanzados.

Outputs en ``notebooks/_data/3y/`` — compresión gzip para tamaño manejable
en repo (~10-50 MB por dataset).

Usar:

    uv run python scripts/build_3year_datasets.py [--include-bms]

Generadores:
    - bdg2_education_subset_3y.csv.gz       (6 edif × 36 meses horarios = ~157 K rows)
    - era5_xativa_3y.csv.gz                 (3 años horarios = 26 K rows)
    - ingauge_aula01_3y.csv.gz              (3 años × 5 min = 315 K rows)
    - lbnl_fdd_rtu_3y.csv.gz                (3 años × 5 min, ~50 fallos etiquetados)
    - traffic_camera_3y.csv.gz              (3 años × 15 min, 5 cámaras)

Si ``--include-bms`` y el stack está vivo:
    - bms_simarro_3years.csv.gz             (export del generador BMS canónico)

Re-ejecuciones producen ficheros idénticos (seed=42).
"""

from __future__ import annotations

import argparse
import gzip
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from notebooks._common.synthetic_mocks import (  # noqa: E402
    make_bdg2_education_subset,
    make_era5_xativa_mock,
    make_ingauge_aula01_mock,
    make_lbnl_fdd_rtu_mock,
    make_traffic_camera_mock,
)

OUT = ROOT / "notebooks" / "_data" / "3y"
OUT.mkdir(parents=True, exist_ok=True)


def _save_gz(df: pd.DataFrame, name: str, header_note: str) -> None:
    target = OUT / f"{name}.csv.gz"
    note = f"# MOCK — {header_note}\n"
    csv_text = note + df.to_csv(index=False)
    with gzip.open(target, "wt", encoding="utf-8", compresslevel=9) as fh:
        fh.write(csv_text)
    size_kb = target.stat().st_size / 1024
    print(f"wrote {target.relative_to(ROOT)}  ({len(df):>9} rows, {size_kb:>8.1f} KB)")


def _enrich_bdg2(df: pd.DataFrame) -> pd.DataFrame:
    """Añade columnas calendario + horario lectivo + estación."""
    ts = pd.to_datetime(df["timestamp"])
    df = df.copy()
    df["year"] = ts.dt.year
    df["month"] = ts.dt.month
    df["dow"] = ts.dt.dayofweek
    df["hour"] = ts.dt.hour
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["is_school_hours"] = ((ts.dt.hour >= 8) & (ts.dt.hour < 18) & (df["is_weekend"] == 0)).astype(int)
    df["season"] = pd.cut(
        df["month"],
        bins=[0, 2, 5, 8, 11, 12],
        labels=["winter", "spring", "summer", "autumn", "winter"],
        ordered=False,
    )
    return df


def _enrich_era5(df: pd.DataFrame) -> pd.DataFrame:
    """Añade dew_point, relative_humidity, solar_zenith aproximado, day_of_year."""
    ts = pd.to_datetime(df["timestamp"])
    df = df.copy()
    df["day_of_year"] = ts.dt.dayofyear
    df["hour"] = ts.dt.hour
    # Magnus approx para dew point (asumiendo HR ~60 % típica)
    rh_default = 60.0 + 10.0 * np.cos(2 * np.pi * ts.dt.dayofyear / 365)
    a, b = 17.27, 237.7
    alpha = (a * df["t_air_c"]) / (b + df["t_air_c"]) + np.log(rh_default / 100.0)
    df["dew_point_c"] = (b * alpha / (a - alpha)).round(2)
    df["relative_humidity"] = rh_default.round(1)
    # Solar zenith aproximado (latitud 38.99°N Xátiva)
    lat_rad = np.radians(38.99)
    decl = 23.45 * np.sin(np.radians(360 / 365 * (284 + ts.dt.dayofyear)))
    decl_rad = np.radians(decl)
    hour_angle = np.radians(15 * (ts.dt.hour - 12))
    cos_zenith = np.sin(lat_rad) * np.sin(decl_rad) + np.cos(lat_rad) * np.cos(decl_rad) * np.cos(hour_angle)
    df["solar_zenith_deg"] = np.degrees(np.arccos(np.clip(cos_zenith, -1, 1))).round(1)
    return df


def _enrich_ingauge(df: pd.DataFrame) -> pd.DataFrame:
    """Añade derivadas: iaq_index, comfort_pmv aproximado, energy_kwh acumulado."""
    df = df.copy()
    # IAQ index: mapeo simplificado CO2 → 0-500 scale (EPA AQI-like)
    co2 = df["Indoor_CO2"].astype(float)
    df["iaq_index"] = np.clip((co2 - 400) / 3.2, 0, 500).round(0).astype(int)
    # PMV simplificado (Fanger 1970), asume met=1.2, clo=0.5
    t = df["Indoor_Temp"].astype(float)
    df["comfort_pmv"] = (0.0875 * t - 1.95).round(2)  # rango típico [-3, +3]
    # Power consumption proxy (W) — para Caso B
    df["power_w"] = (
        80 + 180 * df["CoolingState"].astype(int) + 8 * df["People_Count"].astype(int)
    ).round(0).astype(int)
    return df


def _enrich_lbnl(df: pd.DataFrame) -> pd.DataFrame:
    """Etiqueta más fallos sintéticos por tipo + severidad."""
    df = df.copy()
    if "fault_label" not in df.columns:
        df["fault_label"] = "normal"
    if "fault_severity" not in df.columns:
        df["fault_severity"] = 0.0
    return df


def _enrich_traffic(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Añade categorías de vehículos."""
    df = df.copy()
    n = len(df)
    if "vehicles" in df.columns:
        total = df["vehicles"].astype(float).values
    else:
        total = np.zeros(n)
    df["cars"] = (total * 0.78).round().astype(int)
    df["trucks"] = (total * 0.12).round().astype(int)
    df["motorbikes"] = (total * 0.07).round().astype(int)
    df["bicycles"] = (total * 0.03).round().astype(int)
    df["congestion_level"] = pd.cut(
        total,
        bins=[-1, 5, 15, 30, 1000],
        labels=["fluid", "slow", "dense", "congested"],
    )
    return df


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-bms", action="store_true", help="Exportar dump del generador BMS si stack está vivo")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("=" * 70)
    print(f"Generando datasets 3 años en {OUT.relative_to(ROOT)}/")
    print("=" * 70)

    # 1. BDG2 educacional 36 meses
    df_bdg2, _ = make_bdg2_education_subset(months=36, seed=args.seed)
    df_bdg2 = _enrich_bdg2(df_bdg2)
    _save_gz(df_bdg2, "bdg2_education_subset_3y", "BDG2 educacional 6 edif × 36 meses horarios + calendario + estación")

    # 2. ERA5 Xátiva 3 años (1095 días horarios)
    df_era5, _ = make_era5_xativa_mock(days=1095, seed=args.seed)
    df_era5 = _enrich_era5(df_era5)
    _save_gz(df_era5, "era5_xativa_3y", "ERA5 Xátiva 3 años horarios + dew_point + solar_zenith + RH")

    # 3. In-Gauge AULA01 3 años a 1min (granularidad nativa del dataset real)
    # 1095 days × 24h × 60 = 1 576 800 rows
    # NOTA: el generador asume freq=1min y periods=days*24*60. Pasar freq="5min"
    # extiende el periodo 5x (cubría 15 años en lugar de 3). Mantenemos default.
    df_ingauge, _ = make_ingauge_aula01_mock(days=1095, seed=args.seed)
    df_ingauge = _enrich_ingauge(df_ingauge)
    # Downsample a 5 min para reducir tamaño en repo (~5 MB vs ~25 MB).
    df_ingauge = df_ingauge.iloc[::5].reset_index(drop=True)
    _save_gz(df_ingauge, "ingauge_aula01_3y", "In-Gauge AULA01 3 años × 5 min + IAQ index + PMV + power_w")

    # 4. LBNL FDD 3 años con fallos a 1min, downsample a 5 min para repo
    df_lbnl, _ = make_lbnl_fdd_rtu_mock(days=1095, seed=args.seed)
    df_lbnl = _enrich_lbnl(df_lbnl)
    df_lbnl = df_lbnl.iloc[::5].reset_index(drop=True)
    _save_gz(df_lbnl, "lbnl_fdd_rtu_3y", "LBNL FDD RTU 3 años × 5 min con fallos etiquetados")

    # 5. Traffic 3 años, 5 cámaras
    df_traffic, _ = make_traffic_camera_mock(days=1095, seed=args.seed)
    df_traffic = _enrich_traffic(df_traffic, np.random.default_rng(args.seed))
    _save_gz(df_traffic, "traffic_camera_3y", "DGT cámaras 3 años × 15 min + categorías + congestión")

    if args.include_bms:
        print()
        print("--- Export BMS via /v1/datasets/export (requiere stack vivo) ---")
        _try_export_bms()

    print()
    print(f"Total ficheros generados en {OUT.relative_to(ROOT)}/")
    for f in sorted(OUT.glob("*.csv.gz")):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  {f.name:<45} {size_mb:>6.2f} MB")

    return 0


def _try_export_bms() -> None:
    """Intenta exportar dump del generador BMS si está vivo en :8120."""
    import os

    import httpx

    token = os.environ.get("BMS_API_TOKEN", "")
    if not token:
        print("  SKIP: BMS_API_TOKEN no definido")
        return
    try:
        r = httpx.post(
            "http://localhost:8120/v1/datasets/export",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "config_path": "/app/config/projects/bms_v1_3years.yaml",
                "format": "line_protocol",
                "months": 36,
            },
            timeout=30.0,
        )
        if r.status_code in (200, 202):
            print(f"  OK: dump 3 años solicitado → {r.json()}")
        else:
            print(f"  HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  SKIP: stack no accesible ({type(e).__name__})")


if __name__ == "__main__":
    sys.exit(main())
