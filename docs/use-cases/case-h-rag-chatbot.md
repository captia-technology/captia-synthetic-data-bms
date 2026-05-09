# Caso H — RAG, agentes IA y chatbot

> **Última verificación:** 2026-05-10
> **Audiencia:** equipo G1 (Sergio, Ainhoa, Guillermo, Jordi).
> **Capa Medallion primaria:** consume plata, produce oro (tools + RAG).
> **Notebooks:** 5 (`notebooks/08_case_H_rag_chatbot/`).

## Objetivo

Construir un chatbot que responde preguntas sobre el edificio combinando:

- **Tools sobre InfluxDB** para datos numéricos precisos
  (`query_influxdb`, `compare_periods`, `get_building_state`).
- **Tools mocked → reales** para predicciones (`get_weather_prediction`,
  `get_consumption_prediction`, `check_hvac_anomaly`).
- **RAG documental** para conocimiento general (normativa OMS, CENTINELA+,
  Medallion).

## Datos esperados

- **InfluxDB** de cada equipo (consumido vía tools).
- **Documentos RAG** en `notebooks/_data/docs_rag_seed/` (12 markdowns).
- **Golden set** en `notebooks/_data/chatbot_golden_set.csv` (40 preguntas).

## Capas Medallion

| Capa | Contenido |
|---|---|
| Bronce | docs markdown, golden set CSV |
| Plata | (consumida desde InfluxDB) |
| Oro | tools registradas, índice TF-IDF, golden set evaluado |

## Notebooks asociados

1. `01_arquitectura_rag_tools.ipynb` — decisión: pregunta → tool o RAG.
2. `02_tools_influxdb.ipynb` — implementación `query_influxdb`,
   `compare_periods`, `get_building_state`.
3. `03_mock_tools_modelos_predictivos.ipynb` — mocks para B/C/E con firma
   estable.
4. `04_rag_documental.ipynb` — TF-IDF + cosine sobre 12 docs.
5. `05_evaluacion_chatbot.ipynb` — golden set + métricas.

## Tools mínimas

| Tool | Uso | Fuente |
|---|---|---|
| `query_influxdb` | Valor agregado | Caso H mismo |
| `compare_periods` | Diferencia entre 2 períodos | Caso H mismo |
| `get_building_state` | Estado actual AULA01 | Caso H + Caso D |
| `get_weather_prediction` | Predicción meteo 24 h | Caso E (G3) |
| `get_consumption_prediction` | Predicción consumo | Caso B (G1 mismo) |
| `check_hvac_anomaly` | Anomalía HVAC | Caso C (G3) |

## Estrategia de mocks

Semanas 1-2: tools con mocks plausibles. Semana 3: sustituir mocks por
modelos reales sin cambiar firma. La firma es contrato.

## Validación

- Routing accuracy > 0.6 sobre golden set.
- Recall@5 RAG > 0.6 sobre las 16 preguntas de categoría `rag`.
- Hallucination rate < 0.2 (heurística).

## Errores comunes

1. **Indexar valores numéricos en ElasticSearch** (incorrecto, usar tool).
2. **Mockear con firma distinta** a la versión real — bloquea integración.
3. **No registrar trazabilidad** de qué tool eligió el LLM.
4. **Golden set pequeño / no diverso**.

## Reutilización con datos reales

El chatbot accede a `simarro-prod` cambiando `INFLUXDB_*` en `.env`. Los
documentos RAG se enriquecen con material real del IES Simarro.

## Coordinación con otros casos

- **Caso B** (mismo equipo) — `get_consumption_prediction` consume el
  modelo entrenado en B.
- **Caso C** (G3) — `check_hvac_anomaly` consume el detector de C.
- **Caso E** (G3) — `get_weather_prediction` consume el predictor de E.
- **Caso D** (G4) — `get_building_state` lee del InfluxDB de D.
- **Caso G** — el agente evaluador audita las respuestas del chatbot.
