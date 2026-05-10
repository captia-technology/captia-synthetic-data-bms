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

## Marco teórico (nivel doctoral)

### Modelo IAQ (EN 16798-1:2019)

El índice de calidad del aire interior CO₂ se modela como un sistema de
balance de masa "well-mixed" (un solo compartimento):

\[
V \frac{dC(t)}{dt} = N(t) \cdot G - Q(t) \cdot (C(t) - C_{out})
\]

donde:
- $V$ = volumen del aula (m³).
- $C(t)$ = concentración CO₂ interior (ppm).
- $C_{out}$ = concentración CO₂ exterior $\approx 420$ ppm.
- $N(t)$ = ocupación instantánea (personas).
- $G$ = tasa de generación CO₂ por persona (4.5 ppm·m³/min·persona, ASHRAE 62.1).
- $Q(t)$ = tasa de ventilación (m³/min).

Solución estacionaria con $N$ constante y $Q$ constante:

\[
C_\infty = C_{out} + \frac{N \cdot G}{Q}
\]

Para clase típica Simarro ($V = 180$ m³, $N = 25$, $Q = 7.5$ m³/min con
HVAC ON, $G = 4.5$): $C_\infty \approx 570$ ppm. Sin ventilación
($Q \to 0$) la concentración crece sin asíntota hasta clipping a 2 200 ppm.

### Modelo de ocupación (Random Forest)

\[
\hat{N} = \text{RF}(\mathbf{x}), \quad \mathbf{x} = [C, T, RH, \text{noise}, \text{lux}, \text{hour}, \text{dow}]
\]

con $\text{RF} = \frac{1}{B} \sum_{b=1}^{B} T_b(\mathbf{x})$ ensemble de
$B = 100$ árboles entrenados con bootstrap.

Métrica: F1 binario sobre `Occupied` ($N > 0$). Objetivo $\text{F1} \geq 0.8$.

### Confort térmico (modelo PMV simplificado)

Predicted Mean Vote (Fanger 1970):

\[
\text{PMV} = (0.303 e^{-0.036 M} + 0.028) (M - W - H_{loss})
\]

donde $M$ = tasa metabólica, $W$ = trabajo mecánico, $H_{loss}$ pérdida de calor.

Para aulas (sentado, ropa ligera, $M \approx 70$ W/m², $W \approx 0$):

\[
\text{PMV}_{aula} \approx 0.234 \cdot (70 - H_{loss}(T, RH, v_{air}))
\]

con objetivos PMV $\in [-0.5, +0.5]$ para banda de confort.

## ROI del Caso D

| Concepto | Valor anual |
|---|---|
| Reducción consumo HVAC (15 %) por ajuste IAQ | +1 162 €/año |
| Reducción quejas alumnos / profesores | +500 €/año (productividad) |
| **Beneficio bruto** | **+1 662 €/año** |
| Coste implantación dashboard IAQ | -800 € one-time |
| **Payback** | **~6 meses** |

## Bibliografía

- ASHRAE 62.1-2019 — Ventilation for Acceptable Indoor Air Quality.
- EN 16798-1:2019 — Energy performance of buildings.
- Fanger, P. O. (1970). *Thermal Comfort*. McGraw-Hill.
- In-Gauge Dataset — [github.com/InGauge-au/InGauge-Dataset](https://github.com/InGauge-au/InGauge-Dataset).
- UCI Occupancy Detection — [archive.ics.uci.edu/ml/datasets/Occupancy+Detection+](https://archive.ics.uci.edu/ml/datasets/Occupancy+Detection+).
