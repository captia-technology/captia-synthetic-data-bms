# Casos de uso

> **Última verificación:** 2026-05-10
> **Fuente de verdad:** `docs/audit/USE_CASE_MATRIX.md`

El proyecto cubre 10 casos de uso (A–J) más un caso extra de evaluación de
chatbot. Cada caso tiene su propia página con explicación, datos, capas
Medallion, notebooks asociados y errores comunes.

## Tabla resumen

| Caso | Página | Equipo | Capa primaria | Notebooks |
|---|---|---|---|---|
| A — Pipeline IoT | [case-a-pipeline-iot](case-a-pipeline-iot.md) | (asignación pendiente) | bronce → plata | 3 |
| B — Forecast consumo 24h | [case-b-energy-forecasting](case-b-energy-forecasting.md) | G1 | oro | 5 |
| C — Anomalías HVAC | [case-c-hvac-anomaly](case-c-hvac-anomaly.md) | G3 | plata + oro | 5 |
| D — IAQ + ocupación | [case-d-iaq-occupancy](case-d-iaq-occupancy.md) | G4 | bronce → oro | 5 |
| E — Meteo & solar | [case-e-weather-solar](case-e-weather-solar.md) | G3 | bronce → oro | 4 |
| F — MLOps | [case-f-mlops](case-f-mlops.md) | G4 | transversal | 3 |
| G — Calidad con agentes | [case-g-data-quality-agents](case-g-data-quality-agents.md) | G2/G4 | transversal | 4 |
| H — RAG + Chatbot | [case-h-rag-chatbot](case-h-rag-chatbot.md) | G1 | oro | 5 |
| I — Spark vs Pandas | [case-i-spark-pandas](case-i-spark-pandas.md) | G2 | bronce → plata | 4 |
| J — Tráfico + YOLO | [case-j-traffic-yolo](case-j-traffic-yolo.md) | G5 | bronce → oro | 4 |

## Cómo leer una página de caso

Cada `case-*.md` sigue una estructura común:

1. **Objetivo** — qué resuelve el caso.
2. **Audiencia** — quién lo lleva.
3. **Datos** — bronce esperado y mocks.
4. **Capas Medallion** — qué se transforma de bronce a plata y a oro.
5. **Schema CAPTIA aplicado** — tags y variables relevantes.
6. **Notebooks** — enlace directo a cada `.ipynb`.
7. **Modelos** — técnicas y librerías usadas.
8. **Validación** — criterios de aceptación.
9. **Errores comunes y reutilización con datos reales**.

## Decisiones tomadas

- Caso A se mantiene como código de referencia incluso si en este curso no
  se asigna a un grupo (G2 evalúa migrar al Caso G).
- Caso F se cubre como notebooks documentales: el stack `make demo` no
  arranca un servidor MLflow para mantener el repo ligero. El alumno puede
  ejecutar MLflow con backend SQLite local.
- Caso E e I dependen de datos externos (ERA5, BDG2 completo); los
  notebooks llegan a oro con mocks deterministas y documentan cómo
  reemplazar por datos reales.
- Caso H usa **mocks** para los modelos predictivos (semanas 1–2). En
  semana 3 se sustituyen por las implementaciones reales sin tocar las
  firmas de las tools.
