# Datos para los notebooks didácticos

Esta carpeta contiene **mocks deterministas** y **golden sets** para que los
notebooks puedan ejecutarse sin descargar datasets externos ni levantar el
stack. Todos los ficheros con sufijo `_mock.csv` son sintéticos y se
generan vía `notebooks/_common/synthetic_mocks.py` con `seed=42`.

## Inventario

| Fichero | Generador | Caso | Notas |
|---|---|---|---|
| `ingauge_aula01_mock.csv` | `make_ingauge_aula01_mock` | A, D | 7 días × 1min, schema In-Gauge / En-Gage. |
| `bdg2_education_subset_mock.csv` | `make_bdg2_education_subset` | B, I | 6 edificios × 12 meses horarios. |
| `lbnl_fdd_rtu_mock.csv` | `make_lbnl_fdd_rtu_mock` | C, G | 14 días × 1min con 4 fallos etiquetados. |
| `era5_xativa_mock.csv` | `make_era5_xativa_mock` | E, B, H | 30 días horarios T, GHI, viento, lluvia, presión. |
| `traffic_camera_mock.csv` | `make_traffic_camera_mock` | J | 7 días × 15min en 2 cámaras DGT mock. |
| `chatbot_golden_set.csv` | `make_chatbot_golden_set` | H, G | 40 preguntas con categoría y mecanismo esperado. |
| `docs_rag_seed/*.md` | escritos a mano | H | 12 documentos para el ejemplo RAG. |

## Generación

Los `.csv` se materializan mediante el script
`scripts/build_notebook_data.py` (que invoca los generadores deterministas).
Re-ejecutar produce ficheros idénticos byte a byte.

> **Importante:** los datasets reales (BDG2, In-Gauge, LBNL FDD, ERA5,
> AEMET, DGT) **no** se incluyen en el repo por tamaño y licencia; los
> mocks tienen una nota explícita `# MOCK — sintético, no representa
> datos reales` en su primera línea.
