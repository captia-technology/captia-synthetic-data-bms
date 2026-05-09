# Cómo ejecutar los notebooks

> **Última verificación:** 2026-05-10

## Prerrequisitos

- **Python 3.12+** disponible (gestionado vía `uv`).
- **`uv`** instalado (`pipx install uv`).
- **Stack opcional** levantado (`make demo` o `task up`) si quieres
  ejecutar los notebooks `needs-stack`.

## Instalación

```bash
git clone https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS
cd CAPTIA-SYNTHETIC-DATA-BMS
uv sync --all-extras
cp .env.example .env
# (regenerar tokens en .env con `openssl rand -hex 32`)
```

## Generar mocks deterministas (sólo la primera vez)

```bash
uv run python scripts/build_notebook_data.py
```

Esto crea/regenera los CSV en `notebooks/_data/` (los mismos bytes con
`seed=42`).

## Lanzar JupyterLab

```bash
uv run --with jupyterlab --with ipykernel jupyter lab notebooks/
```

JupyterLab abrirá un navegador en `http://localhost:8888`. El kernel
recomendado es **Python 3.12** del entorno `.venv` del repo.

## Modos de ejecución

| Modo | Reconocer | Cómo correr |
|---|---|---|
| `ready` | el notebook funciona solo con numpy/pandas/matplotlib y mocks | abre y ejecuta `Run All` |
| `needs-stack` | requiere InfluxDB / Mosquitto | `make demo` antes de `Run All` |
| `mocked` | usa mocks por defecto, switch a real con `.env` | edita `.env` y reinicia kernel |

Para forzar modo offline en cualquier notebook:

```bash
echo "INFLUX_OFFLINE=true" >> .env
```

## VS Code

Si prefieres VS Code:

1. Instala la extensión Jupyter.
2. Abre el repo y selecciona el kernel **Python 3.12 (.venv)**.
3. `Run All` en cualquier `.ipynb`.

## Errores frecuentes

- **`ImportError: notebooks._common`** — ejecuta Jupyter desde la raíz
  del repo, no desde `notebooks/`.
- **`KeyError: INFLUXDB_URL`** — copia `.env.example` a `.env` y
  reinicia kernel.
- **`influxdb_client` no instalado** — los notebooks tienen fallback
  offline; instala con `uv pip install influxdb-client` para conexiones
  reales.
- **Plots vacíos** — confirma backend `%matplotlib inline` (Jupyter por
  defecto).

## Reproducibilidad

Re-ejecutar cualquier notebook con `seed=42` produce los mismos
resultados. Si dos ejecuciones no coinciden, consulta
[`docs/use-cases/case-f-mlops.md`](../use-cases/case-f-mlops.md).
