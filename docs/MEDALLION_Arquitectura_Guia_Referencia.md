# Arquitectura Medallion aplicada a CENTINELA+
## Guía de referencia para el proyecto final IES Simarro 2025-26

---

## 1. ¿Qué es la arquitectura Medallion?

La arquitectura Medallion (también llamada *Multi-hop architecture* o *lakehouse pattern*) es un patrón de diseño de datos que organiza el procesamiento en **capas sucesivas de refinamiento**. Cada capa tiene una calidad y un propósito diferente, y los datos fluyen de una capa a la siguiente siendo transformados y enriquecidos progresivamente.

El nombre "Medallion" viene de los metales: bronce, plata y oro. La analogía es precisa: el bronce es abundante y en bruto; la plata ya está refinada y tiene una forma útil; el oro es el producto final de mayor valor, específico para un propósito concreto.

```
CAPA BRONCE          →      CAPA PLATA           →      CAPA ORO
(datos crudos)              (datos normalizados)         (datos enriquecidos)

CSV, JSON, MQTT             Schema canónico              Features para ML
Payloads de sensores        Mismas unidades              Embeddings para RAG
Logs de gateway             Tags consistentes            Agregaciones para KPIs
Datos sin validar           Valores validados            Conjuntos de entrenamiento
```

---

## 2. Las tres capas en detalle

### 2.1 Capa Bronce — datos en origen

**¿Qué contiene?** Los datos tal como llegan de la fuente, sin ninguna transformación. Su única garantía es que son auténticos y están preservados.

**Características:**
- Formato original de la fuente (CSV, JSON, MQTT payload, NetCDF, ZIP).
- Pueden tener errores, nulos, duplicados, formatos inconsistentes, unidades distintas.
- No se modifican nunca: son la fuente de verdad histórica.
- Se versionan en un sistema de control de versiones de datos (lakeFS, DVC, Delta Lake).

**Principio fundamental:** si algo sale mal en una capa posterior, siempre se puede volver a la capa bronce y recomputar desde ahí.

**En el proyecto:**
- Los datasets públicos en su formato original: `electricity.csv` de BDG2, los ficheros ZIP del LBNL FDD, los CSV de In-Gauge/En-Gage, los NetCDF de ERA5, las imágenes de las cámaras DGT.
- Versionados en lakeFS con un commit y un tag etiquetado en el momento de la descarga.

---

### 2.2 Capa Plata — datos normalizados y validados

**¿Qué contiene?** Los datos transformados a un schema común, validados, con las unidades convertidas y listos para análisis.

**Características:**
- Schema homogéneo y consistente: todos los datos tienen la misma estructura independientemente de su origen.
- Valores validados: nulos tratados, rangos comprobados, duplicados eliminados.
- Unidades convertidas al sistema de referencia del proyecto.
- Identificadores consistentes: los mismos IDs para las mismas entidades en todos los datasets.
- Timestamps normalizados a UTC en nanosegundos epoch.

**En el proyecto:**
- El InfluxDB local de cada equipo con el **schema canónico de CAPTIA**: measurement `captia_point`, 5 tags (`captia_env`, `domain_id`, `site_id`, `asset_id`, `variable`), field `value` (float).
- El catálogo `captia_metadata` poblado con las variables del dataset.
- Los buckets de rollup (`telemetry_1m`, `telemetry_15m`, `telemetry_1h`) generados por las Flux tasks.

**Ejemplo de transformación bronce → plata para In-Gauge/En-Gage:**
```
BRONCE (CSV original):
  timestamp,classroom_id,IndoorTemperature,IndoorHumidity,IndoorCO2
  2022-01-10 08:15:00,room_01,21.3,58.2,612

PLATA (InfluxDB con schema CAPTIA):
  captia_point,captia_env=prod,domain_id=bms_classrooms,
    site_id=ies_simarro,asset_id=AULA01,variable=temperature-indoor
    value=21.3 1641802500000000000
```

La transformación resuelve: renombrado de columnas, asignación de tags, conversión de timestamp a nanosegundos, clasificación entre señales continuas y on-change.

---

### 2.3 Capa Oro — datos enriquecidos para casos de uso específicos

**¿Qué contiene?** Conjuntos de datos derivados de la capa plata, enriquecidos con las transformaciones específicas que necesita cada caso de uso.

**Características:**
- Orientada a un propósito concreto (entrenamiento de un modelo, una visualización, un índice de búsqueda).
- Puede contener features calculadas, predicciones de modelos anteriores, embeddings, indicadores de calidad, etc.
- Puede ser un DataFrame en pandas, un fichero Parquet, un índice en ElasticSearch, un conjunto de datos en lakeFS, o incluso un experimento registrado en MLflow.
- Es la capa que evoluciona más durante el proyecto a medida que los equipos refinan sus modelos.

**En el proyecto, cada equipo tiene su propia capa oro:**

| Equipo | Capa oro |
|--------|----------|
| G1-B (Predicción consumo) | DataFrame con features temporales (hora, día semana, lag 24h) + variable objetivo `power_01` |
| G1-H (Chatbot) | Índice ElasticSearch con embeddings de documentos + datos ERA5 como context de tools |
| G3-C (Anomalías HVAC) | Dataset con señales HVAC + etiquetas de fallo → cargado en lakeFS |
| G3-E (Meteorología) | Serie temporal ERA5 en InfluxDB (dominio weather_station) + modelo FV entrenado |
| G4-D (Calidad aire) | DataFrame pivotado con CO₂, T, HR, ruido + etiqueta de ocupación |
| G4-F (MLOps) | Artefactos MLflow + tags lakeFS de todos los datasets del proyecto |
| G4-G (Calidad con agentes) | Reglas de calidad ejecutables + informes de validación por dataset |
| G2-G (Calidad) | Ídem |

---

## 3. CAPTIA como capa plata operacional

Una característica especial de este proyecto es que **CAPTIA ya ha resuelto internamente el paso de bronce a plata**. El InfluxDB de simarro-prod no es bronce — es ya una capa plata: los datos llegan estructurados en measurement, tags, field value, con agregaciones temporales y con el catálogo de variables en `captia_metadata`.

```
CENTINELA+ en producción:

[Sensores físicos]          [CAPTIA internamente]          [InfluxDB simarro-prod]
  bronce real         →        bronce → plata         →       CAPA PLATA real
(payloads MQTT)          (Telegraf + normalización)        (schema canónico CAPTIA)
```

Para el proyecto, esto significa:

- **El schema de InfluxDB de CAPTIA es nuestra capa plata de referencia.** Todos los equipos deben tener una capa plata local que replica ese schema.
- **El Caso A (Pipeline IoT) simula el proceso bronce → plata** que CAPTIA realiza con sensores reales. Su valor educativo es precisamente enseñar cómo se construye ese proceso.
- **El resto de equipos construyen su capa plata** cargando sus datasets públicos en el schema de CAPTIA (sin necesitar Mosquitto ni Telegraf — pueden insertar directamente).
- **Las capas oro** son las ETLs y transformaciones específicas de cada caso de uso, construidas sobre esa capa plata común.

---

## 4. Las tres variantes de la arquitectura Medallion

### Variante 1 — Medallion estricto (académico)

Todas las capas se procesan de forma secuencial y centralizada. Un único pipeline gobierna todo el flujo.

```
Bronce          →    Plata          →    Oro
(lago de datos      (data warehouse     (data marts
 centralizado)       normalizado)        por dominio)
```

**Ventaja:** coherencia total, fácil de auditar.
**Inconveniente:** requiere infraestructura centralizada desde el día 1.
**¿Aplica al proyecto?** Solo parcialmente: la centralización completa no es viable con los plazos del proyecto.

---

### Variante 2 — Medallion distribuido (por equipo)

Cada equipo gestiona su propio stack de capas. La capa plata es local y se carga independientemente. La integración ocurre en una fase posterior.

```
Equipo A:  [BDG2 bronce] → [InfluxDB plata local] → [features oro para modelo B]
Equipo B:  [ERA5 bronce]  → [InfluxDB plata local] → [documentos oro para chatbot]
Equipo C:  [FDD bronce]   → [InfluxDB plata local] → [dataset oro con etiquetas]
```

**Ventaja:** máxima autonomía, sin cuellos de botella.
**Inconveniente:** los datos de distintos equipos no son directamente comparables hasta que se consolidan.
**¿Aplica al proyecto?** Sí, en las semanas 1-2.

---

### Variante 3 — Medallion híbrido (la elegida para este proyecto)

Trabajo distribuido en las primeras semanas + consolidación centralizada en las últimas.

```
Semanas 1-2:           Semanas 3-4:
[Distribuido]    →     [Consolidación]    →    [Demo final]

Cada equipo tiene      InfluxDB central        Integración
su capa plata local.   (equipo A o infra        entre capas
Cada equipo            compartida ITI).         oro de todos
construye su capa oro. Todos conectan.          los equipos.
```

**Ventaja:** sin dependencias iniciales + integración final posible.
**Inconveniente:** requiere que todos usen variables de entorno para la conexión (cambio de `.env`, no de código).
**¿Aplica al proyecto?** Sí. Esta es la estrategia adoptada.

---

### Variante 4 — Medallion con capa plata de arranque (situación negociando con Captia)

En lugar de que cada equipo construya su capa plata desde cero, se parte de un **InfluxDB de arranque** ya cargado con datos representativos. Cada equipo restaura ese dump y construye directamente su capa oro.

```
[Dump InfluxDB plata]    →    [Restore local por equipo]    →    [Capa oro por equipo]
(provisto por CAPTIA          (docker load + influx restore)      (ETL específica
 o por los profesores)                                             de cada caso)
```

**Ventaja:** los equipos empiezan a trabajar sobre datos reales desde el primer día sin ETL inicial.
**Inconveniente clave para este proyecto:** depende de que CAPTIA pueda proporcionar datos suficientemente buenos para TODOS los casos de uso — incluyendo predicción ML, anomalías HVAC etiquetadas y datos meteorológicos — lo cual es incierto dado que el sistema de CAPTIA no usa modelos predictivos.
**¿Aplica al proyecto?** Condicionalmente: si CAPTIA puede proporcionar el dump, se adopta. Si no, se mantiene la variante híbrida (3).

---

## 5. La arquitectura Medallion del proyecto: resumen visual

```
─────────────────────────────────────────────────────────────────────────
CAPA BRONCE — Datasets públicos originales (lakeFS)
─────────────────────────────────────────────────────────────────────────
  G1-B: BDG2 (electricity.csv, weather.csv) + UCI Appliances (CSV)
  G1-H: ERA5 (NetCDF) + documentos de contexto (texto plano)
  G3-C: LBNL FDD (ZIP con CSVs de subsistemas HVAC)
  G3-E: ERA5 (NetCDF) + SARAH-3 (opcional, NetCDF)
  G4-D: In-Gauge/En-Gage (16 CSV) + UCI Occupancy (TXT)
  G2-G: Todos los datasets anteriores (para auditoría de calidad)
  G5-J: Imágenes cámaras DGT (JPEG) + AEMET (JSON/CSV)
─────────────────────────────────────────────────────────────────────────
                              ↓ ETL (cada equipo)
─────────────────────────────────────────────────────────────────────────
CAPA PLATA — InfluxDB local con schema CAPTIA (cada equipo)
─────────────────────────────────────────────────────────────────────────
  measurement: captia_point
  5 tags: captia_env, domain_id, site_id, asset_id, variable
  1 field: value (float)
  9 buckets: telemetry, _1m, _15m, _1h, state_events, captia_metadata...
─────────────────────────────────────────────────────────────────────────
                              ↓ ETL gold (cada equipo)
─────────────────────────────────────────────────────────────────────────
CAPA ORO — Artefactos específicos por caso de uso
─────────────────────────────────────────────────────────────────────────
  G1-B: DataFrame con features temporales + lag → modelo SARIMA/XGBoost/LSTM
  G1-H: Índice ElasticSearch + tools InfluxDB → chatbot con agentes
  G3-C: Dataset HVAC + etiquetas fallo → Isolation Forest / Autoencoder
  G3-E: Serie meteorológica + modelo predicción solar → tool del chatbot
  G4-D: DataFrame IAQ + etiqueta ocupación → clasificador Random Forest
  G4-F: Artefactos MLflow + tags lakeFS → reproducibilidad del proyecto
  G2-G: Reglas Great Expectations + informes de calidad → validación cruzada
  G5-J: Conteos YOLOv por cámara en InfluxDB → modelo predicción congestión
─────────────────────────────────────────────────────────────────────────
                              ↓ Integración (semanas 3-4)
─────────────────────────────────────────────────────────────────────────
INTEGRACIÓN FINAL — InfluxDB centralizado + demo conjunta
─────────────────────────────────────────────────────────────────────────
  Chatbot (H) llama a modelos de predicción (B, E) y anomalías (C)
  QA (G) audita calidad de datos de todos los equipos
  MLOps (F) garantiza trazabilidad y reproducibilidad de todos los experimentos
  Demo unificada en Grafana con datos de todos los grupos
─────────────────────────────────────────────────────────────────────────
```

---

## 6. El Caso A como el único grupo que recorre todo el medallion

El Caso A (Pipeline IoT con Mosquitto, InfluxDB y Grafana) tiene un papel especial: **es el único que simula el paso completo bronce → plata tal como ocurre en CENTINELA+ real**, incluyendo la publicación MQTT, la recepción en Mosquitto y la ingesta mediante Telegraf.

```
CASO A — El recorrido completo de CENTINELA+ simulado:

[Dataset CSV]   →   [Script Python]   →   [Mosquitto MQTT]   →   [Telegraf]   →   [InfluxDB]
 capa bronce         simula sensor         broker real            pipeline          capa plata
                     publicando            de CENTINELA+          de ingesta        real de
                                                                                    CENTINELA+
```

Este recorrido es el que hace CENTINELA+ con sensores reales. Cuando el IES Simarro tenga datos reales, bastará con apuntar el mismo Telegraf al Mosquitto real del edificio y el pipeline seguirá funcionando sin cambios.

El valor pedagógico del Caso A es precisamente enseñar cómo está construido el sistema real. Su documentación y su código quedarán como referencia para cursos futuros y como base para escalar CENTINELA+ a nuevas aulas.

---

## 7. ¿Qué cambia con la arquitectura Medallion respecto a los documentos anteriores?

| Concepto anterior | Concepto Medallion |
|-------------------|-------------------|
| "Dataset público" | Capa Bronce |
| "Ingesta en InfluxDB con schema CAPTIA" | Paso Bronce → Plata (ETL) |
| "InfluxDB local con schema CAPTIA" | Capa Plata |
| "Features para ML / embeddings para RAG" | Capa Oro |
| "InfluxDB centralizado (semanas 3-4)" | Consolidación de capas plata |
| "Script de bootstrap de buckets" | Inicialización de la capa plata |

El código y los notebooks no cambian. Solo cambia el vocabulario con el que describimos el proceso, y ese vocabulario aporta claridad conceptual y conecta el proyecto con la práctica real de la ingeniería de datos.
