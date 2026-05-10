"""Run all notebooks in `notebooks/` and report PASS/FAIL.

Usage:
    uv run python scripts/run_all_notebooks.py [--timeout 180]

Generates:
    docs/audit/NOTEBOOK_EXECUTION_REPORT.md with per-notebook results.

The runner uses ``jupyter nbconvert --to notebook --execute`` with each
notebook's directory as cwd so relative paths to ``_data`` and
``_common`` work as expected. Notebooks that require live services
(MQTT, InfluxDB) read connection params from ``.env``; if the stack
is down those notebooks are skipped (marked SKIP).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
REPORT_PATH = REPO_ROOT / "docs" / "audit" / "NOTEBOOK_EXECUTION_REPORT.md"


def find_notebooks() -> list[Path]:
    return sorted(
        nb for nb in NOTEBOOKS_DIR.rglob("*.ipynb")
        if ".ipynb_checkpoints" not in nb.parts
    )


def run_notebook(nb: Path, timeout: int) -> dict:
    rel = nb.relative_to(REPO_ROOT)
    started = time.time()
    cmd = [
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "notebook",
        "--execute",
        "--inplace",
        f"--ExecutePreprocessor.timeout={timeout}",
        "--ExecutePreprocessor.kernel_name=python3",
        str(nb),
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout + 60,
            env={
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
                "MPLBACKEND": "Agg",
                # Force notebooks to use mock data instead of trying to reach
                # http://influxdb:8086 (Docker DNS) from the host runner. The
                # _common.connection helper returns None when this is set, and
                # all notebooks have a `if client is None` fallback path.
                "INFLUX_OFFLINE": "true",
            },
        )
        elapsed = time.time() - started
        if result.returncode == 0:
            status = "PASS"
            error = ""
        else:
            status = "FAIL"
            error_lines = (result.stderr or result.stdout).strip().splitlines()
            # Buscar líneas de error útiles
            relevant = [
                ln for ln in error_lines
                if any(kw in ln for kw in ("Error", "Traceback", "FAILED", "raise", "raised"))
            ]
            error = "\n".join(relevant[-8:]) if relevant else "\n".join(error_lines[-5:])
    except subprocess.TimeoutExpired:
        elapsed = time.time() - started
        status = "TIMEOUT"
        error = f"timeout after {timeout}s"

    return {
        "notebook": str(rel).replace("\\", "/"),
        "status": status,
        "elapsed_s": round(elapsed, 2),
        "error": error,
    }


def write_report(results: list[dict], started_at: datetime) -> None:
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    n_timeout = sum(1 for r in results if r["status"] == "TIMEOUT")
    total = len(results)
    total_secs = sum(r["elapsed_s"] for r in results)

    lines = [
        "# Auditoría — Reporte de ejecución de notebooks",
        "",
        f"> **Generado:** {started_at.isoformat()}",
        f"> **Total notebooks:** {total}",
        f"> **PASS:** {n_pass} · **FAIL:** {n_fail} · **TIMEOUT:** {n_timeout}",
        f"> **Tiempo total:** {total_secs/60:.1f} min ({total_secs:.0f} s)",
        "",
        "## Resumen por caso de uso",
        "",
        "| Caso | PASS | FAIL | TIMEOUT | Tiempo (s) |",
        "|---|---:|---:|---:|---:|",
    ]
    by_case: dict[str, dict] = {}
    for r in results:
        case = r["notebook"].split("/", 2)[1] if "/" in r["notebook"] else "(root)"
        d = by_case.setdefault(case, {"PASS": 0, "FAIL": 0, "TIMEOUT": 0, "elapsed": 0.0})
        d[r["status"]] = d.get(r["status"], 0) + 1
        d["elapsed"] += r["elapsed_s"]
    for case, d in sorted(by_case.items()):
        lines.append(
            f"| `{case}` | {d['PASS']} | {d['FAIL']} | {d['TIMEOUT']} | "
            f"{d['elapsed']:.0f} |"
        )

    lines += [
        "",
        "## Detalle por notebook",
        "",
        "| Notebook | Status | Tiempo (s) | Error (resumen) |",
        "|---|---|---:|---|",
    ]
    for r in results:
        err_short = (r["error"][:140].replace("\n", " ") + "…") if len(r["error"]) > 140 else r["error"].replace("\n", " ")
        emoji = {"PASS": "✅", "FAIL": "❌", "TIMEOUT": "⏱"}.get(r["status"], "⚠")
        lines.append(
            f"| `{r['notebook']}` | {emoji} {r['status']} | "
            f"{r['elapsed_s']:.1f} | {err_short or '—'} |"
        )

    if n_fail or n_timeout:
        lines += ["", "## Errores completos", ""]
        for r in results:
            if r["status"] != "PASS":
                lines += [
                    f"### `{r['notebook']}` — {r['status']}",
                    "",
                    "```",
                    r["error"][:2000],
                    "```",
                    "",
                ]

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--filter", type=str, default="", help="substring filter")
    args = parser.parse_args()

    notebooks = find_notebooks()
    if args.filter:
        notebooks = [nb for nb in notebooks if args.filter in str(nb)]
    print(f"Found {len(notebooks)} notebooks", flush=True)

    started_at = datetime.now(UTC)
    results: list[dict] = []
    for i, nb in enumerate(notebooks, 1):
        rel = nb.relative_to(REPO_ROOT)
        print(f"[{i}/{len(notebooks)}] {rel}", end=" ", flush=True)
        r = run_notebook(nb, args.timeout)
        emoji = {"PASS": "OK", "FAIL": "FAIL", "TIMEOUT": "TIMEOUT"}.get(r["status"], "?")
        print(f"{emoji} ({r['elapsed_s']:.1f}s)", flush=True)
        if r["status"] != "PASS" and r["error"]:
            print(f"    {r['error'][:200]}", flush=True)
        results.append(r)

    write_report(results, started_at)
    print(f"\nReport written to {REPORT_PATH}")

    n_fail = sum(1 for r in results if r["status"] != "PASS")
    print(f"PASS={len(results) - n_fail}/{len(results)}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
