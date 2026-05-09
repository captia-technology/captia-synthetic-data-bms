# Índice IAQ (Indoor Air Quality)

El índice IAQ combina varios contaminantes y condiciones ambientales en
un único valor 0–500. Implementación BME680 (Bosch):

- 0–50 — excelente.
- 51–100 — bueno.
- 101–150 — ligeramente contaminado.
- 151–200 — moderadamente contaminado.
- 201–300 — fuertemente contaminado.
- 301–500 — extremadamente contaminado.

Los inputs habituales son CO₂ equivalente, t-VOC, temperatura, humedad y
algoritmo propietario de calibración. Para CENTINELA+ se publica como
`variable=iaq_index` con `metric_kind=analog_gauge` y rango 0–500.
