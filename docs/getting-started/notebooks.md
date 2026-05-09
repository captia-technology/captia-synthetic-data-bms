# Empezar con los notebooks didácticos

> **Última verificación:** 2026-05-10

## Pasos para una primera ejecución

1. Sigue [Setup local](local-setup.md).
2. Genera mocks deterministas:
   ```bash
   uv run python scripts/build_notebook_data.py
   ```
3. Lanza JupyterLab desde la raíz del repo:
   ```bash
   uv run --with jupyterlab --with ipykernel jupyter lab notebooks/
   ```
4. Abre `notebooks/00_project_overview/00_arquitectura_medallion_captia.ipynb`
   y ejecuta `Run All`.

## Orden recomendado

1. **00 Overview** (3 notebooks, ~45 min) — orientación obligatoria.
2. **Caso A** (3 notebooks, ~20 min) — entender el pipeline real.
3. **Caso de tu equipo** (B/C/D/E completos, 4–5 h).
4. **Caso F** cuando empiece la fase de modelos.
5. **Caso G** en paralelo desde semana 1.
6. **Caso H** una vez que tengas un modelo entrenado.
7. **Casos I y J** opcionales / paralelos.

## Modos de ejecución

- **`ready`** — funciona sin stack levantado.
- **`needs-stack`** — `make demo` previo.
- **`mocked`** — funciona con mocks; switch a real con `.env`.

## Recursos

- [Mapa de notebooks](../notebooks/notebook-map.md).
- [Cómo ejecutar los notebooks](../notebooks/how-to-run.md).
- [Plan completo](../audit/NOTEBOOK_PLAN.md).
