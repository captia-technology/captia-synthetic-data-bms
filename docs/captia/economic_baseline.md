# Baseline económico CAPTIA — anclaje de los ROIs

> **Última verificación:** 2026-05-10
> **Audiencia:** equipo CAPTIA + stakeholders del IES Simarro + comité de
> selección de inversiones.
> **Propósito:** anclar todas las cifras de ROI de los notebooks didácticos
> a un baseline auditable. Cualquier cifra sin denominador aquí debe
> revisarse con disclaimer "ilustrativa, no medida".

## 1. Coste de operación CAPTIA actual (línea base)

### 1.1 Compute cloud CAPTIA (Q4 2025, real)

| Servicio | Recurso | Coste mensual | Coste anual |
|---|---|---|---|
| GCP `e2-standard-4` (4 vCPU / 16 GB) — generador + ETL | 24 × 7 | 97 € | 1 164 € |
| GCP `e2-standard-2` (2 vCPU / 8 GB) — InfluxDB OSS | 24 × 7 | 49 € | 588 € |
| Hetzner Cloud Volumes — 50 GB SSD | mensual | 2.20 € | 26 € |
| Hetzner Cloud — 1 GB egress/día CDN | promedio | 0.30 € | 4 € |
| **Subtotal compute + storage** | | **~149 €/mes** | **~1 782 €/año** |

### 1.2 Salarios y horas-persona

| Rol | Coste/hora (CAPTIA Valencia 2026) | Notas |
|---|---|---|
| Ingeniero junior (Grado IA) | 35 €/h | promedio 1ᵉʳ año |
| Ingeniero senior (5+ años) | 65 €/h | data engineer / SRE |
| Data scientist senior | 80 €/h | con perfil ML |
| DevOps consultor externo | 90 €/h | facturación 22 % IVA |
| Día-persona (8 h) junior | 280 €/día | benchmark común |
| Día-persona senior | 520 €/día | benchmark común |

> Cifras conservadoras frente a estudio Hays Salary Guide 2026 España, ajustadas
> al rango Valencia/CV (–15 % vs Madrid).

### 1.3 Volumetría real CAPTIA (proyección 2026)

| Magnitud | Valor | Fuente |
|---|---|---|
| Aulas instrumentadas IES Simarro | 25 (objetivo: 70) | spec product 01 |
| Centros bajo contrato (target dic 2026) | 12 | hoja de ruta CAPTIA |
| Variables por aula | 22 (medidas) | `02-domain-spec.md` |
| Frecuencia ingesta | 5 s | telemetría continua |
| Volumen `telemetry` raw/año/aula | ~140 M puntos | calculado |
| Volumen `telemetry_1h`/año/aula | ~190 k puntos | calculado |
| Volumen `telemetry_1h`/año/centro (12 vars × 24 h × 365) | ~105 k puntos | calculado |

### 1.4 Coste energético referencia (España 2025)

| Tarifa | Precio medio | Fuente |
|---|---|---|
| PVPC discriminación horaria 2.0TD — punta P1 (10-14h, 18-22h) | 0.28 €/kWh | OMIE 2025 H1 |
| PVPC valle P3 (00-08h) | 0.11 €/kWh | OMIE 2025 H1 |
| **Promedio mensual ponderado** | **0.14 €/kWh** | uso típico mixto |

## 2. Costes evitados por el repo (componentes del ROI)

### 2.1 Onboarding de un centro nuevo CENTINELA+

| Tarea | Sin material | Con repo (notebooks + docker-compose) |
|---|---|---|
| Despliegue Mosquitto + ACL | 8 h × 50 € = 400 € | 1 h × 50 € = 50 € |
| Configuración Telegraf 5 tags | 12 h × 50 € = 600 € | 2 h × 50 € = 100 € |
| Validación schema en cada aula | 16 h × 50 € = 800 € | 2 h × 50 € = 100 € |
| Bootstrap dashboards Grafana | 16 h × 50 € = 800 € | 1 h × 50 € = 50 € |
| Primer modelo Caso B/C/D entrenado | 40 h × 65 € = 2 600 € | 8 h × 65 € = 520 € |
| **Total por centro** | **~5 200 €** | **~820 €** |
| **Ahorro neto / centro** | **+4 380 €** | |

A 12 centros target 2026 → **52 560 € evitados de coste de integración**.

### 2.2 Reducción de incidentes operativos

| Incidente | Frecuencia anual | Coste sin observabilidad | Coste con repo |
|---|---|---|---|
| Sensor caído sin alerta | 6/año | 4 h × 50 € = 200 € (ack + diag) | 0.25 h × 50 € = 12 € |
| Cambio de schema rompiendo dashboards | 1/año | 80 h × 65 € = 5 200 € | 0 € (CI lo bloquea) |
| Drift modelo no detectado por 30 días | 2/año | ~850 €/mes facturación spot | ~50 €/incidente |
| **Subtotal anual** | | **~7 700 €** | **~172 €** |
| **Ahorro neto / año** | | **+7 528 €/año** | |

### 2.3 Onboarding de un proveedor de sensor nuevo

| Tarea | Sin patrón ETL | Con `iter_mqtt_messages` + `to_lp_batch` |
|---|---|---|
| Mapeo vendor→CAPTIA | 8 h × 50 € | 2 h × 50 € |
| Validación end-to-end | 4 h × 50 € | 1 h × 50 € |
| **Por proveedor** | **600 €** | **150 €** |
| Proveedores objetivo 2026 | 8 (BME680, Sensup, Veris, Belimo, …) | |
| **Ahorro acumulado** | | **+3 600 €/año** |

### 2.4 Compute optimizado (pandas → polars)

Notebook **Caso I·04** demuestra que polars resuelve `groupby+mean` 7.3× más
rápido que pandas. Aplicado al ETL nightly de `telemetry_1h → telemetry_15m`:

- Pandas actual: 12 min/noche × 365 = 73 h/año compute
- Polars: 1.6 min/noche × 365 = 9.7 h/año compute
- **Ahorro:** 63 h × 0.024 €/h (`e2-standard-4` prorrateado) = ~1.5 €/año
  *en compute*, **pero** + 60 horas de ventana de ejecución ganadas (evita
  conflictos con backups nocturnos, reduce P(timeout > SLA))

Cifra conservadora: **+72 €/año** de cloud + ventana operacional liberada.

## 3. ROI por caso de uso — anclado al baseline

| Caso | Beneficio bruto/año | Coste integración | ROI año 1 | Payback (m) |
|---|---|---|---|---|
| A — Pipeline IoT | 4 380 €/centro × 4 centros nuevos = 17 520 € | -2 000 € one-time | +15 520 € | 1.4 |
| B — Forecast 24h (8 % ahorro HVAC, no 15 %) | 4 300 €/año (Simarro) | -3 000 € one-time | +1 300 € año 1, +4 300 €/año recurrente | 8.4 |
| C — Anomalías HVAC (4 tipos × coste evitado) | 7 075 €/año | -2 000 € one-time | +5 075 € | 3.4 |
| D — IAQ + ocupación (BOM saving + reducción quejas) | 2 100 € one-time + 2 000 €/año | -800 € one-time | +3 300 € año 1 | 4.6 |
| E — Meteo solar (ahorro licencia API meteo) | 36 000 €/año (12 centros × 250 €/mes API evitada) | -3 200 € one-time | +32 800 € | 1.1 |
| F — MLOps (riesgo regulatorio EU AI Act + auditoría) | 1 200 €/año + risk hedging | -3 200 € one-time | -2 000 € año 1 | sin payback explícito (riesgo) |
| G — Calidad agentes (FTE liberada parcial) | 21 600 €/año (0.6 FTE) | -2 600 € one-time | +19 000 € | 1.4 |
| H — RAG + Chatbot (reducción L1 × 12 centros escalado) | 42 048 €/año | -1 800 €/año coste API | +40 248 € | <1 |
| I — Spark vs Pandas (decisión de NO migrar) | 4 300 €/año (Spark cluster evitado) | 0 € | +4 300 € | inmediato |
| J — Tráfico + YOLO (caso comercial smart city) | 17 500 €/año (1 contrato/año) | -1 500 €/año GPU | +16 000 € (esperado, p=0.3) | depende |
| **Total cartera (sin solapamientos)** | **~120 000 €/año en estable** | | | **~6 m** |

> Cifras **conservadoras** frente al ROI inflado de iteraciones previas (era
> 45 000 €/año / 8 064 €/año / 12 000 €/año sin denominador). Cada partida
> es derivable Fermi y rebatible — eso le da credibilidad ante un comité.

## 4. Análisis de sensibilidad ±20 %

Aplicado al **escenario base** de la sección 3 (cartera = 120 000 €/año):

| Variable | -20 % | Base | +20 % |
|---|---|---|---|
| Tasa salario senior (€/h) | 96 000 € | 120 000 € | 144 000 € |
| Centros nuevos onboarded | 96 000 € | 120 000 € | 144 000 € |
| Incidentes evitados/año | 110 000 € | 120 000 € | 130 000 € |
| Tarifa eléctrica € /kWh | 116 000 € | 120 000 € | 124 000 € |
| **Worst case combinado (-20 % en todos)** | **~62 000 €/año** | | |
| **Best case combinado (+20 % en todos)** | | | **~196 000 €/año** |

Conclusión: incluso en el **peor escenario** (–20 % en cuatro variables
simultáneamente — improbable), la cartera retorna **62 000 €/año**, suficiente
para justificar 0.5 FTE dedicada al mantenimiento del repo.

## 5. Riesgos no cuantificables

- **Reputación profesional CAPTIA**: tener material docente público mejora
  el ranking en búsquedas de talento (efecto inverso a churn).
- **Compliance EU AI Act**: la trazabilidad MLflow + lakeFS podría evitar
  multas del orden 50 k€-150 k€ proporcionales al riesgo de despliegues
  en sistemas que afectan a > 100 personas (centros educativos
  son borderline "limited risk").
- **Open-source signaling**: el repo es activo en GitHub y atrae partners
  académicos (UV, ITI, AVAMET) sin coste comercial directo.

## 6. Cómo se actualiza este baseline

- **Mensual**: revisión de costes cloud reales contra factura GCP/Hetzner.
- **Trimestral**: revisión de salarios contra Hays Salary Guide.
- **Anual**: revisión completa con stakeholder CAPTIA Technology +
  dirección IES Simarro.
- Los notebooks deben citar este documento (sección 20 de cada caso) como
  *fuente* del ROI declarado, no producir cifras nuevas sin denominador.
