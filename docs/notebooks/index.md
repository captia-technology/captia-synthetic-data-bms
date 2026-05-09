# Notebooks didácticos

> **Última verificación:** 2026-05-10
> **Carpeta:** `notebooks/` (45 notebooks).
> **Plan completo:** [`audit/NOTEBOOK_PLAN.md`](../audit/NOTEBOOK_PLAN.md).

Material docente del Curso de Especialización IA & Big Data IES Simarro.
Cada notebook es **didáctico, ejecutable y con mocks deterministas**, no
un script. La estructura sigue 18 secciones obligatorias documentadas en
[`notebooks/_common/template_outline.md`](https://github.com/captia-technology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/notebooks/_common/template_outline.md).

## Cómo se navega

- **Por caso de uso** — [`docs/use-cases/`](../use-cases/index.md) lista
  cada caso con sus notebooks asociados.
- **Por carpeta** — [`notebook-map.md`](notebook-map.md) tabla con todos.
- **Por tema** — la documentación de contratos, validación y arquitectura
  enlaza a los notebooks relevantes desde cada sección.

## Pasos previos

1. [Cómo ejecutar los notebooks](how-to-run.md).
2. Confirmar `.env` con credenciales y `seed=42`.
3. (Opcional) Levantar el stack `make demo` si trabajas con
   notebooks `needs-stack`.

## Convenciones

- **`seed=42`** declarado al inicio.
- **Mocks etiquetados** con `# MOCK — sintético`.
- Cada notebook lleva `> _Caso de uso: X · Capa Medallion: Y · Spec: ...`.

## Cobertura por caso

| Caso | Carpeta | Notebooks |
|---|---|---|
| Overview | `00_project_overview/` | 3 |
| A — Pipeline IoT | `01_case_A_pipeline_iot/` | 3 |
| B — Forecast | `02_case_B_energy_forecasting/` | 5 |
| C — Anomalías | `03_case_C_hvac_anomaly_detection/` | 5 |
| D — IAQ | `04_case_D_iaq_occupancy/` | 5 |
| E — Meteo | `05_case_E_weather_solar/` | 4 |
| F — MLOps | `06_case_F_mlops/` | 3 |
| G — Calidad | `07_case_G_data_quality_agents/` | 4 |
| H — RAG | `08_case_H_rag_chatbot/` | 5 |
| I — Spark | `09_case_I_spark_vs_pandas/` | 4 |
| J — Tráfico | `10_case_J_traffic_yolo/` | 4 |

**Total: 45 notebooks** + helpers en `notebooks/_common/` + mocks en
`notebooks/_data/`.
