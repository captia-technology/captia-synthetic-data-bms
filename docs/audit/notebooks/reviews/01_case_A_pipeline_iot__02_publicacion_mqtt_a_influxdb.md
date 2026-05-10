# Review — `notebooks/01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb`

> **Auditoría:** 2026-05-10  
> **Caso de uso:** Pipeline IoT  
> **Etapa:** 02 (Bronce → Plata (ETL))  
> **Capa Medallion declarada:** bronce → plata  
> **Spec:** `docs/specs/synthetic-bms/03-architecture-spec.md`  
> **Score:** **8.6 / 10** · Veredicto **B** · Prioridad **OK**

## Ficha técnica

| Campo | Valor |
|---|---|
| Ruta | `notebooks/01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb` |
| Título | Publicación MQTT a InfluxDB — del CSV al broker en velocidad acelerada |
| Celdas md / code | 23 / 8 |
| Secciones distintas | 22 |
| Outputs persistidos | 8 / 8 (100.0%) |
| Helpers `_common` | `captia_schema`, `connection`, `plotting`, `synthetic_mocks` |
| Cita schema CAPTIA | sí |
| `assert` presente | sí |
| Mocks etiquetados | sí |
| Sin secretos inline | sí |
| Sin paths absolutos | sí |
| Datasets detectados | In-Gauge AULA01 (sintético) |

## 1. Resumen ejecutivo

<!-- AUTO -->
Notebook **02_publicacion_mqtt_a_influxdb** del caso **Pipeline IoT**, etapa **02** (capa Bronce → Plata (ETL)). Score **8.6/10**, veredicto **B**. 8/8 celdas de código con outputs persistidos (100.0%). Sin bugs P0/P1 reportados. Helpers `_common` reutilizados: `captia_schema`, `connection`, `plotting`, `synthetic_mocks`.

## 2. Propósito del notebook

**Publicación MQTT a InfluxDB — del CSV al broker en velocidad acelerada**.  
Demuestra el camino completo MQTT → Telegraf → InfluxDB con paho-mqtt real y fallback in-memory. Mide throughput contra λ teórico CENTINELA+ (308 msg/s).

## 3. Caso de uso asociado

- **Dominio:** Pipeline IoT.
- **Caso CAPTIA Synthetic Data BMS:** `01_case_A_pipeline_iot`.
- **Spec asociado:** `docs/specs/synthetic-bms/03-architecture-spec.md`.
- **Capa Medallion:** bronce → plata.

## 4. Nivel didáctico esperado

**Nivel:** I ({B=básico, I=intermedio, A=avanzado}).

<!-- TODO: justificar nivel con prerequisitos del notebook -->

## 5. Qué funciona bien

- Estructura de **22 secciones** (target 22).
- Cita explícita del schema canónico CAPTIA.
- Helpers `_common` reutilizados (`captia_schema`, `connection`, `plotting`, `synthetic_mocks`).
- Outputs persistidos celda a celda (100.0%).
- `assert`-driven validación.

**Curado:** Errores comunes específicos a `paho-mqtt` (sec 17, NA-04 ausente). Setup determinista. Throughput medido vs λ teórico es insight real.

## 6. Problemas técnicos

- _Sin bugs P0/P1 conocidos._

**Curado:** Sec 19 (LaTeX) decorativa: cita teoría queueing pero el código no calcula λ ni ρ. Sin tabla decisional QoS 0/1/2.

## 7. Problemas didácticos

**Curado:** Falta justificar **por qué** QoS=1 en CENTINELA+. Alumno no aprende cuándo subir/bajar QoS.

## 8. Problemas de reproducibilidad

- verificar manualmente.
- Sin paths absolutos.
- Sin secretos inline.

<!-- TODO: validar `INFLUX_OFFLINE` fallback funciona; idempotencia del setup; determinismo. -->

## 9. Problemas de estilo corporativo CAPTIA.ai

<!-- TODO: comprobar tono, terminología, links a economic_baseline, alineación CENTINELA+. -->

## 10. Problemas de arquitectura Medallion

- **Capa declarada:** bronce → plata.
- **Etapa:** 02 (Bronce → Plata (ETL)).

<!-- TODO: ¿lee bronce sin mutar? ¿escribe plata respetando schema? ¿genera oro reutilizable? -->

## 11. Problemas de schema CAPTIA / CENTINELA+

- **Cita schema:** sí
- **Helpers schema utilizados:** sí

<!-- TODO: validar que tags son exactamente los 5 canónicos; measurement único `captia_point`. -->

## 12. Riesgos para alumnos

<!-- TODO: identificar conceptos confusos, terminología cambiante, saltos didácticos. -->

## 13. Riesgos para uso profesional

<!-- TODO: ¿es defendible ante un auditor externo? ¿el ROI es trazable? ¿hay leakage? -->

## 14. Cambios recomendados

<!-- TODO: lista priorizada con líneas concretas o helpers a invocar -->

1. _(añadir cambio 1)_
2. _(añadir cambio 2)_
3. _(añadir cambio 3)_

## 15. Prioridad

**OK** — mantener.

## 16. Veredicto

**B** — _Bueno, requiere mejora_.

## Scorecard detallado (auditoría deep-9 / Sprints)

Pedag 6 · Código 7 · Rigor 5 · Visu 4 · Ejer 5 · ErrCom 7 · ROI 5 · Reuso 8 · Coher 6 → **6.6**

## Datasets utilizados

- In-Gauge AULA01 (sintético)

## Patrones NA-* aplicables

<!-- TODO: marcar cuáles de NA-A..NA-H + NA-01..NA-10 aplican a este notebook concreto -->

## Referencias

- Auditoría detallada: [`../../NOTEBOOK_AUDIT_DETAILED.md`](../../NOTEBOOK_AUDIT_DETAILED.md)
- Auditoría inicial deep-9: [`../../NOTEBOOK_AUDIT.md`](../../NOTEBOOK_AUDIT.md)
- Baseline económico: [`../../../captia/economic_baseline.md`](../../../captia/economic_baseline.md)
- Plan de uso: [`../../NOTEBOOK_PLAN.md`](../../NOTEBOOK_PLAN.md)
- Matriz casos de uso: [`../../USE_CASE_MATRIX.md`](../../USE_CASE_MATRIX.md)
