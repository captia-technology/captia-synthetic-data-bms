# Schema canónico CAPTIA

Toda la telemetría continua de CENTINELA+ vive en un único measurement de
InfluxDB: `captia_point`. Cada punto tiene 1 field (`value`, float) y 5
tags indexados:

- `captia_env` ∈ {dev, staging, prod}
- `domain_id` (p.ej. `bms_classrooms`, `bms_buildings`, `weather_station`,
  `traffic_cameras`)
- `site_id` (p.ej. `ies_simarro`, `bdg2_education`, `xativa`, `valencia`)
- `asset_id` (p.ej. `AULA01`, `bdg2_bldg_03`, `era5_gridpoint`,
  `DGT_CAM_V46_001`)
- `variable` (p.ej. `co2`, `power_01`, `solar_irradiance`)

Estados booleanos se codifican como 1.0 (activo) y 0.0 (inactivo).

Las etiquetas de fallo HVAC del Caso C viven en un measurement separado
`captia_fault_labels` (bucket `state_events`, retención 90 d) para no
contaminar `captia_point`.
