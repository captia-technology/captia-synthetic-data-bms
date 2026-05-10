# STATUS — Auditoría profesional de notebooks CAPTIA

> **Última actualización:** 2026-05-10
> **Generado por:** `scripts/audit_notebooks.py --status`

## Checklist de entregables

### 1. Documentos en `docs/audit/notebooks/`

- [x] **9 / 9** documentos creados
  - [x] `00_NOTEBOOK_INVENTORY.md` (18,264 bytes)
  - [x] `CAPTIA_NOTEBOOK_GUIDELINES.md` (23,827 bytes)
  - [x] `CAPTIA_NOTEBOOK_TEMPLATE.md` (7,214 bytes)
  - [x] `NOTEBOOK_QUALITY_MATRIX.md` (13,848 bytes)
  - [x] `NOTEBOOK_REFACTOR_PLAN.md` (12,589 bytes)
  - [x] `THEMATIC_REVIEW.md` (22,390 bytes)
  - [x] `FINAL_NOTEBOOK_AUDIT_REPORT.md` (14,155 bytes)
  - [x] `REFACTOR_EXECUTION_REPORT.md` (15,541 bytes)
  - [x] `STATUS.md` (2,282 bytes)

### 2. Reviews por notebook (`reviews/<case>_<nb>.md`)

- [x] **45 / 45** reviews creados

### 3. Template canónico

- [x] `notebooks/_templates/CAPTIA_NOTEBOOK_TEMPLATE.ipynb`

### 4. Scripts auxiliares

- [x] **2 / 2** scripts
  - [x] `scripts/audit_notebooks.py`
  - [x] `scripts/build_notebook_template.py`

## Métricas globales

- **Notebooks totales:** 45 / 45
- **Score medio:** 8.22 / 10 (baseline 6.31)
- **Top-3:** `04_case_D_iaq_occupancy/04_modelo_ocupacion_desde_ambiente.ipynb` (9.6), `03_case_C_hvac_anomaly_detection/04_isolation_forest_autoencoder.ipynb` (9.3), `02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb` (8.8)
- **Bottom-3:** `01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb` (7.6), `07_case_G_data_quality_agents/02_reglas_calidad_plata_influxdb.ipynb` (7.6), `02_case_B_energy_forecasting/05_validacion_modelo_24h.ipynb` (7.7)

## Re-validación

```bash
uv run python scripts/audit_notebooks.py --inventory --matrix --reviews-skeleton --status
uv run --group notebooks python scripts/execute_notebooks.py --workers 2 --timeout 300
uv run pytest tests/integration/test_notebooks_integrity.py -q
uv run ruff check . && uv run ruff format --check .
uv run --with mkdocs-material mkdocs build
uv run python scripts/audit_notebooks.py --score-delta
uv run python scripts/audit_notebooks.py --bottom 10 --threshold 7.5
```

> **Workers=2 recomendado** — workers=4 causa race conditions en lecturas
> simultáneas a `output/case_C/hvac_features.parquet`.
