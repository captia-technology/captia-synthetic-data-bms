"""Ejecuta los 45 notebooks didácticos in-place y emite un reporte.

Uso:

    uv run python scripts/execute_notebooks.py [--filter SUBSTR] [--timeout SEC]
                                                [--workers N] [--continue-on-error]
                                                [--report PATH]

Estrategia:
- Usa nbclient para ejecutar cada `.ipynb` en un kernel Python 3.12 limpio.
- Sets `INFLUX_OFFLINE=true` para que los notebooks `needs-stack` usen mocks.
- Captura excepciones por celda y produce un JSON con resultado por notebook.
- Marca cada notebook con tags ``executed`` o ``failed`` en la metadata.
- Re-ejecuciones son seguras (idempotentes en el resultado del notebook).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError, CellTimeoutError

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_DIR = ROOT / "notebooks"


def execute_one(
    nb_path_str: str,
    timeout: int,
    save_in_place: bool,
) -> dict[str, Any]:
    """Ejecuta un solo notebook y devuelve un diccionario con el resultado.

    Devuelve siempre un dict — nunca lanza para que el ProcessPoolExecutor
    agregue resultados sin abortar.
    """
    nb_path = Path(nb_path_str)
    rel = nb_path.relative_to(ROOT).as_posix()
    started = time.perf_counter()
    result: dict[str, Any] = {"notebook": rel, "ok": False, "duration_s": 0.0}

    # Forzar modo offline para que tools de InfluxDB usen mocks
    env = {**os.environ, "INFLUX_OFFLINE": "true", "PYTHONIOENCODING": "utf-8"}
    os.environ.update(env)

    try:
        nb = nbformat.read(nb_path, as_version=4)
        client = NotebookClient(
            nb,
            timeout=timeout,
            kernel_name="python3",
            resources={"metadata": {"path": str(ROOT)}},
        )
        client.execute()
        if save_in_place:
            nbformat.write(nb, nb_path)
        result["ok"] = True
    except CellExecutionError as exc:
        # Identificar la celda que falló
        result["error_type"] = "CellExecutionError"
        result["error"] = str(exc)[:600]
        # Buscar la primera celda con outputs de tipo error
        try:
            for idx, cell in enumerate(nb.cells):
                for out in cell.get("outputs", []):
                    if out.get("output_type") == "error":
                        result["error_cell"] = idx
                        result["error_name"] = out.get("ename")
                        result["error_value"] = out.get("evalue")
                        break
                if "error_cell" in result:
                    break
        except Exception:  # noqa: BLE001
            pass
        if save_in_place:
            try:
                nbformat.write(nb, nb_path)
            except Exception:  # noqa: BLE001
                pass
    except CellTimeoutError as exc:
        result["error_type"] = "CellTimeoutError"
        result["error"] = str(exc)[:600]
    except Exception as exc:  # noqa: BLE001
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:600]

    result["duration_s"] = round(time.perf_counter() - started, 2)
    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--filter", default=None, help="Sólo notebooks cuyo path contenga esta subcadena."
    )
    p.add_argument("--timeout", type=int, default=600, help="Timeout por celda (s). Default 600.")
    p.add_argument("--workers", type=int, default=1, help="Procesos paralelos (1 = serie).")
    p.add_argument(
        "--continue-on-error", action="store_true", default=True, help="Continuar tras un fallo."
    )
    p.add_argument("--no-save", action="store_true", help="No escribir outputs en el .ipynb.")
    p.add_argument(
        "--report",
        default=str(ROOT / "output" / "notebook_execution_report.json"),
        help="Ruta del reporte JSON.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    notebooks = sorted(NOTEBOOK_DIR.rglob("*.ipynb"))
    if args.filter:
        notebooks = [nb for nb in notebooks if args.filter in nb.as_posix()]
    if not notebooks:
        print("No notebooks matched the filter.", file=sys.stderr)
        return 1

    print(
        f"Ejecutando {len(notebooks)} notebooks (timeout={args.timeout}s, workers={args.workers})."
    )
    save_in_place = not args.no_save

    results: list[dict[str, Any]] = []
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futures = {
                ex.submit(execute_one, str(nb), args.timeout, save_in_place): nb for nb in notebooks
            }
            for fut in as_completed(futures):
                res = fut.result()
                results.append(res)
                _print_result(res)
    else:
        for nb in notebooks:
            res = execute_one(str(nb), args.timeout, save_in_place)
            results.append(res)
            _print_result(res)
            if not args.continue_on_error and not res["ok"]:
                break

    # Reporte
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "total": len(results),
        "ok": sum(1 for r in results if r["ok"]),
        "failed": sum(1 for r in results if not r["ok"]),
        "results": sorted(results, key=lambda r: r["notebook"]),
    }
    report_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReporte: {report_path.relative_to(ROOT)}")
    print(f"OK: {summary['ok']}  FAIL: {summary['failed']}")

    if summary["failed"]:
        print("\nFallos:")
        for r in summary["results"]:
            if not r["ok"]:
                err = r.get("error_value") or r.get("error", "?")
                cell = r.get("error_cell", "?")
                print(f"  - {r['notebook']} (celda {cell}): {err[:120]}")
        return 2
    return 0


def _print_result(res: dict[str, Any]) -> None:
    icon = "OK" if res["ok"] else "FAIL"
    nb = res["notebook"]
    dur = res["duration_s"]
    if res["ok"]:
        print(f"  [{icon:4s}] {nb}  ({dur:.1f}s)")
    else:
        cell = res.get("error_cell", "?")
        msg = res.get("error_value") or res.get("error", "?")
        print(f"  [{icon:4s}] {nb}  ({dur:.1f}s)  cell={cell}  -> {str(msg)[:90]}")


if __name__ == "__main__":
    sys.exit(main())
