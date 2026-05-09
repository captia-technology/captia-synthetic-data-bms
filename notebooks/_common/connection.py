"""Conexión a InfluxDB con variables de entorno.

Reglas:

- Nunca hardcodear secretos; siempre leer de ``.env`` o variables de
  entorno del proceso.
- Los defaults locales (`localhost`, `simarro-dev-token-2026`) son **solo**
  para que un notebook arranque sin error en una clase con stack levantado;
  no representan credenciales reales.
- Si ``INFLUX_OFFLINE=true`` el cliente devuelve ``None`` y los notebooks
  muestran cómo serían los datos con mocks.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

DEFAULT_INFLUX_URL = "http://localhost:8087"
DEFAULT_INFLUX_TOKEN = "simarro-dev-token-2026"  # noqa: S105 — fallback dev only
DEFAULT_INFLUX_ORG = "captia"
DEFAULT_INFLUX_BUCKET = "telemetry"


def load_env(env_path: str | Path | None = None) -> dict[str, str]:
    """Carga el ``.env`` raíz del repo en ``os.environ`` y lo devuelve.

    Si python-dotenv no está disponible, intenta una lectura mínima propia
    para no obligar a instalar la dependencia en cada notebook.
    """
    repo_root = _find_repo_root()
    target = Path(env_path) if env_path else repo_root / ".env"

    loaded: dict[str, str] = {}
    if not target.exists():
        return loaded

    try:
        from dotenv import dotenv_values, load_dotenv

        load_dotenv(target, override=False)
        loaded = {k: v for k, v in dotenv_values(target).items() if v is not None}
    except ImportError:
        # Fallback minimal parser
        for line in target.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)
            loaded[key] = val
    return loaded


def get_influx_client(*, allow_offline: bool = True) -> Any | None:
    """Devuelve un ``InfluxDBClient`` o ``None`` si ``INFLUX_OFFLINE=true``.

    El llamador debe usar ``client is None`` como señal para mostrar mocks.
    """
    load_env()
    if os.environ.get("INFLUX_OFFLINE", "").lower() in {"1", "true", "yes"}:
        return None

    url = os.environ.get("INFLUXDB_URL", DEFAULT_INFLUX_URL)
    token = os.environ.get("INFLUXDB_TOKEN", DEFAULT_INFLUX_TOKEN)
    org = os.environ.get("INFLUXDB_ORG", DEFAULT_INFLUX_ORG)

    try:
        from influxdb_client import InfluxDBClient

        return InfluxDBClient(url=url, token=token, org=org, timeout=10_000)
    except ImportError:
        if not allow_offline:
            raise
        return None


def build_query_api(client: Any | None) -> Any | None:
    """Devuelve el ``query_api`` del cliente o ``None`` si offline."""
    if client is None:
        return None
    return client.query_api()


def get_default_bucket() -> str:
    load_env()
    return os.environ.get("INFLUXDB_BUCKET", DEFAULT_INFLUX_BUCKET)


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return here.parent
