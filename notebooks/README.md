# Notebooks didácticos — CAPTIA Synthetic Data BMS

> **Audiencia:** alumnos del Curso de Especialización IA & Big Data IES Simarro,
> profesores, mantenedores del repo y futuros equipos CAPTIA / centros que se
> incorporen a la red CENTINELA+.

Esta carpeta contiene **45 notebooks** que cubren los 11 casos de uso del
proyecto. Cada notebook es un material docente completo (markdown abundante,
diagramas, ejercicios), no un script.

## Estructura

```
notebooks/
├── _common/                       # helpers reutilizables (no notebooks)
│   ├── connection.py              # InfluxDB client con .env
│   ├── captia_schema.py           # constantes del schema canónico
│   ├── synthetic_mocks.py         # generadores in-memory deterministas
│   ├── plotting.py                # helpers matplotlib comunes
│   └── template_outline.md        # las 18 secciones obligatorias
├── _data/                         # mocks ligeros y golden sets
├── 00_project_overview/           # 3 notebooks orientación
├── 01_case_A_pipeline_iot/        # 3 notebooks
├── 02_case_B_energy_forecasting/  # 5 notebooks
├── 03_case_C_hvac_anomaly_detection/   # 5
├── 04_case_D_iaq_occupancy/       # 5
├── 05_case_E_weather_solar/       # 4
├── 06_case_F_mlops/               # 3
├── 07_case_G_data_quality_agents/ # 4
├── 08_case_H_rag_chatbot/         # 5
├── 09_case_I_spark_vs_pandas/     # 4
└── 10_case_J_traffic_yolo/        # 4
```

## Reglas

1. **Schema canónico CAPTIA** (medida `captia_point`, 5 tags, field `value`)
   se respeta en cualquier ETL bronce → plata. Importar las constantes desde
   `_common/captia_schema.py`.
2. **Determinismo:** `seed=42` por defecto. Usar
   `numpy.random.default_rng(42)` (no `np.random.seed`).
3. **Sin secretos:** la conexión a InfluxDB lee `.env`; nunca hardcodear.
4. **Mocks etiquetados:** los datasets reales (BDG2, ERA5, In-Gauge, LBNL FDD,
   AEMET) tienen mock pequeño en `_data/` con cabecera explícita
   `# MOCK — sintético, no representa datos reales`.
5. **Ejecutables incrementalmente:** cada celda debe poder ejecutarse en orden
   sin saltos.

## Cómo abrir y ejecutar

```bash
# Instalar dependencias del workspace
uv sync --all-extras

# Lanzar Jupyter Lab en la raíz del repo
uv run --with jupyterlab --with ipykernel jupyter lab notebooks/

# O abrir un notebook concreto desde VS Code
code notebooks/02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb
```

> Si no tienes `jupyterlab` instalado, `uv run --with jupyterlab jupyter lab`
> lo instalará en un entorno aislado sin tocar el lockfile del workspace.

## Modos de ejecución

| Modo | Cómo se reconoce | Ejemplos |
|------|------------------|----------|
| `ready` | El notebook funciona solo con numpy/pandas/matplotlib y los mocks de `_data/`. | `00/00`, `02/01`, `04/03`. |
| `needs-stack` | Requiere `make demo` con InfluxDB / Mosquitto. | `01/02`, `01/03`, `02/02`. |
| `mocked` | Funciona en cualquier entorno; si los servicios reales están disponibles, se documenta cómo cambiar. | `08/02`, `10/02`. |

Los notebooks `needs-stack` siempre incluyen un branch fallback que muestra
los datos esperados sin requerir la conexión.

## Mapa de casos de uso

Ver:

- `docs/audit/USE_CASE_MATRIX.md` — matriz completa de los 11 casos.
- `docs/audit/NOTEBOOK_PLAN.md` — plan detallado por notebook.
- `docs/use-cases/` — una página por caso con explicación, datos, capas.
- `docs/notebooks/notebook-map.md` — tabla con enlaces a cada notebook.

## Reproducibilidad

Cada notebook fija `SEED = 42` al inicio. Re-ejecutar produce los mismos
resultados (validado en CI por la suite de auditoría 198/198 PASS).

## Política de secretos

- Las variables de InfluxDB (`INFLUXDB_URL`, `INFLUXDB_TOKEN`,
  `INFLUXDB_ORG`, `INFLUXDB_BUCKET`) se cargan con `python-dotenv` desde
  `.env`.
- El fichero `.env` está en `.gitignore`.
- En `notebooks/_common/connection.py` hay valores **solo de desarrollo**
  como fallback (`http://localhost:8086`, `simarro-dev-token-2026`); nunca
  poner ahí un token de producción.
