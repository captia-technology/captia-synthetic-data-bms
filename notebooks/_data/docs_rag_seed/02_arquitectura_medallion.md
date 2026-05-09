# Arquitectura Medallion

La arquitectura Medallion organiza los datos en tres capas: bronce (datos
crudos en su formato original), plata (datos normalizados al schema
canónico) y oro (datos enriquecidos para casos de uso específicos).

En el proyecto CAPTIA Synthetic Data BMS:

- **Bronce:** CSV originales de BDG2, ERA5 (NetCDF), In-Gauge / En-Gage,
  LBNL FDD, AEMET, DGT — versionados en lakeFS sin modificar.
- **Plata:** InfluxDB local con `captia_point` + 5 tags + field `value`.
  El schema es idéntico al de la instalación real `simarro-prod`.
- **Oro:** features ML, embeddings RAG, modelos entrenados, indicadores
  de calidad — específicos de cada caso de uso.

Beneficio: si algo falla en oro, se recompila desde plata; si algo falla
en plata, se recompila desde bronce.
