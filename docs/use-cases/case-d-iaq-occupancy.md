# Caso D — Calidad de aire, confort interior y ocupación

> **Última verificación:** 2026-05-10
> **Audiencia:** equipo G4 (María, MJ, Federico, Lucía, José).
> **Capa Medallion primaria:** bronce → oro.
> **Notebooks:** 5 (`notebooks/04_case_D_iaq_occupancy/`).

## Objetivo

Detectar ocupación a partir de variables ambientales (CO₂, T, HR, ruido,
luz) sin sensor de presencia explícito y calcular un IAQ index con alertas
según rangos OMS / EN 16798. Este es el caso más alineado con AULA01 real.

## Datos esperados

- **Bronce primario:** In-Gauge / En-Gage (16 CSV) — mock 1 semana × 1 min
  en `notebooks/_data/ingauge_aula01_mock.csv`.
- **Bronce alternativo:** UCI Occupancy Detection.

## Capas Medallion

| Capa | Contenido | Bucket |
|---|---|---|
| Bronce | `ingauge_aula01.csv` (Indoor_CO2, Indoor_Temp, ...) | filesystem |
| Plata | `captia_point` con `co2`, `temperature_01`, `relative_humidity_01`, `avg_sound_level`, `luminosity`, `iaq_index`, `occupancy` | `telemetry` 1m |
| Oro | DataFrame pivot + clasificador RF + alertas | `output/case_D/` |

## Schema CAPTIA aplicado

| Tag | Valor |
|---|---|
| `captia_env` | `dev` |
| `domain_id` | `bms_classrooms` |
| `site_id` | `ies_simarro` |
| `asset_id` | `AULA01..AULA16` |
| `variable` | `co2`, `temperature_01`, `relative_humidity_01`, `iaq_index`, `occupancy`, `people_count` |

Mapping In-Gauge → CAPTIA en
[`docs/contracts/variable-catalog.md`](../contracts/variable-catalog.md).

## Notebooks asociados

1. `01_eda_iaq_ocupacion.ipynb` — relación CO₂ ↔ ocupación, recreos.
2. `02_bronze_to_silver_iaq.ipynb` — ETL + poblar `captia_point_meta`.
3. `03_features_confort_ocupacion.ipynb` — `dCO2/dt`, IAQ proxy.
4. `04_modelo_ocupacion_desde_ambiente.ipynb` — RF + Logistic.
5. `05_validacion_iaq_confort.ipynb` — alertas OMS / EN 16798.

## Modelos y librerías

- **Random Forest** y **Logistic Regression** para clasificar
  `Occupied` (binario).
- **IAQ index** sintético combinando CO₂, T, HR.
- Comparación con normativa: ver
  [`notebooks/_data/docs_rag_seed/05_co2_aulas_oms.md`](https://github.com/captia-technology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/notebooks/_data/docs_rag_seed/05_co2_aulas_oms.md).

## Validación

- F1 > 0.8 para `occupancy` sobre In-Gauge mock.
- IAQ rangos correctamente categorizados (`óptimo` / `aceptable` / `vigilar`
  / `molesto` / `ventilar`).
- Sin valores fuera de los rangos físicos del catálogo.

## Errores comunes

1. **Confundir `Occupied` (0/1) con `People_Count`** (entero).
2. **Suavizar features que cambian rápido** — picos CO₂ desaparecen.
3. **Threshold único** sin histéresis — alertas oscilantes.
4. **No incluir vacaciones** — el modelo predice mal en julio.

## Reutilización con datos reales

Cuando AULA01 tenga histórico, los notebooks aplican directamente. Las
queries Flux equivalentes son:

```python
flux = '''
from(bucket: "telemetry_1m")
  |> range(start: -30d)
  |> filter(fn: (r) => r.asset_id == "AULA01")
  |> filter(fn: (r) => r.variable == "co2" or r.variable == "occupancy")
  |> filter(fn: (r) => r.stat == "mean")
  |> pivot(rowKey:["_time"], columnKey:["variable"], valueColumn:"_value")
'''
```

## Coordinación con otros casos

- **Caso E** (G3) — coordinar variables exteriores comunes (T, HR, lux).
- **Caso H** (G1) — el modelo se sirve como tool `get_building_state`.
- **Caso G** — auditar balance de clases en el dataset supervisado.
