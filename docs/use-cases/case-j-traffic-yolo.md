# Caso J — Tráfico y visión artificial con YOLOv

> **Última verificación:** 2026-05-10
> **Audiencia:** alumno G5 (Jorge Albert Bosch, en remoto).
> **Capa Medallion primaria:** bronce → oro.
> **Notebooks:** 4 (`notebooks/10_case_J_traffic_yolo/`).

## Objetivo

Capturar imágenes periódicas de cámaras DGT, ejecutar inferencia YOLO
para conteo de vehículos y construir una serie temporal de intensidad de
tráfico correlacionada con AEMET (lluvia, viento).

## Datos esperados

- **Bronce primario:** JPEG cámaras DGT + AEMET JSON.
- **Bronce mock:** `notebooks/_data/traffic_camera_mock.csv` (7 días × 15 min
  × 2 cámaras + lluvia).

## Capas Medallion

| Capa | Contenido | Almacén |
|---|---|---|
| Bronce | JPEG (`cameras/{id}/{date}/{ts}.jpg`) | MinIO (S3 compatible) |
| Plata | `vehicle_count`, `congestion_level`, `detection_confidence` en `captia_point` | InfluxDB `traffic_cameras` |
| Oro | dataset fusionado tráfico × meteo + modelo congestión | `output/case_J/` |

> **Importante:** las imágenes JPEG **no** van a InfluxDB. Solo los conteos
> y derivados numéricos.

## Schema CAPTIA aplicado

| Tag | Valor |
|---|---|
| `captia_env` | `dev` |
| `domain_id` | `traffic_cameras` |
| `site_id` | `valencia` |
| `asset_id` | `DGT_CAM_V46_001`, etc. |
| `variable` | `vehicle_count`, `congestion_level`, `detection_confidence` |

## Notebooks asociados

1. `01_captura_imagenes_dgt.ipynb` — estrategia cron + MinIO + retry.
2. `02_inferencia_yolo.ipynb` — YOLO mock (default), real con `ultralytics`.
3. `03_series_temporales_trafico.ipynb` — ETL conteos a InfluxDB.
4. `04_integracion_meteo_trafico.ipynb` — modelo predicción congestión.

## Modelos y librerías

- **YOLO**: `ultralytics` (opcional). Mock determinista por defecto.
- **Random Forest** ordinal para `congestion_level`.

## Validación

- `vehicle_count ∈ [0, 200]` y entero.
- `detection_confidence ∈ [0, 1]`.
- `congestion_level ∈ {0, 1, 2, 3}`.
- El modelo discrimina los 4 niveles con `balanced_accuracy > 0.5`.

## Errores comunes

1. **Guardar imágenes en InfluxDB** — TSDB para números.
2. **Sobrescribir** si la cámara repite nombre.
3. **No filtrar `confidence < threshold`**.
4. **Cron sin retry** — un fallo intermitente pierde días de serie.

## Reutilización con datos reales

Sustituir `count_vehicles_mock` por `count_vehicles_real` (con
`ultralytics`). Configurar `MINIO_ENDPOINT` y APScheduler para producción
desatendida.

## Coordinación con otros casos

- **Caso E** (G3) — meteorología cruzada (lluvia, viento).
- **Caso H** (G1) — opcional: tool `get_traffic_state(camera)`.
- **Caso F** — versiona las imágenes en lakeFS o MinIO.

## Marco teórico (nivel doctoral)

### YOLO v8 — single-stage detector anchor-free

\[
\hat{y} = (b_x, b_y, b_w, b_h, p_{obj}, p_{class_1}, ..., p_{class_C})
\]

Loss combinada:

\[
\mathcal{L} = \lambda_{box} \mathcal{L}_{CIoU} + \lambda_{obj} \mathcal{L}_{BCE,obj} + \lambda_{cls} \mathcal{L}_{BCE,cls}
\]

### Series temporales tráfico

\[
N_v(t) = \sum_{i=1}^{D_t} \mathbb{1}[\text{detection}_i \in v_{ROI}]
\]

NMS con IoU threshold = 0.5.

### Predictor congestión

\[
\hat{C}(t+15) = \text{XGB}(N_v(t), N_v(t-15), ..., \text{weather}, \text{hour}, \text{dow})
\]

con $C \in \{0,1,2,3\}$ niveles.

### Métricas

\[
\text{mAP@0.5} = \frac{1}{|C|} \sum_{c \in C} \text{AP}_c \, (\text{IoU} \geq 0.5)
\]

Objetivos: mAP@0.5 ≥ 0.90 (car/truck), ≥ 0.75 (motorbike/bicycle).

## ROI Caso J

| Concepto | Valor |
|---|---|
| Predicción congestión 15 min | +5 000 €/año (semáforos) |
| Detección incidentes < 60 s | +12 000 €/año (emergencias) |
| **Bruto** | **+17 000 €/año** |
| Compute GPU dedicada | -1 500 €/año |
| **Neto** | **+15 500 €/año** |

## Bibliografía

- Redmon, J. (2018). *YOLOv3*.
- Ultralytics — [docs.ultralytics.com](https://docs.ultralytics.com).
- DGT cámaras — [infocar.dgt.es](http://infocar.dgt.es).
- COCO Dataset — [cocodataset.org](https://cocodataset.org).
