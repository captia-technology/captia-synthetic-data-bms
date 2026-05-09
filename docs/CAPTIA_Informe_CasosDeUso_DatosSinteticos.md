# Informe técnico para CAPTIA Technology
## Proyecto Final Curso de Especialización en IA y Big Data
## IES Dr. Lluís Simarro — Curso 2025-2026

**Destinatario:** Jaume (CAPTIA Technology)
**Remitente:** Equipo docente IES Dr. Lluís Simarro
**Fecha:** Mayo 2026
**Contexto:** Este informe describe los casos de uso del proyecto final del Curso de Especialización en IA y Big Data del IES Simarro, los datos que necesitamos para abordarlos correctamente, y las capacidades que os pedimos que valoréis para apoyar el proyecto y los cursos futuros.

---

## 1. Contexto del proyecto

El proyecto final del Curso de Especialización en IA y Big Data se desarrolla durante el mes de mayo de 2026. El alumnado trabajará en equipos que aplicarán técnicas de machine learning, Big Data y sistemas de IA generativa sobre datos de edificios inteligentes, con el objetivo de producir desarrollos que sean **directamente reutilizables en CENTINELA+** cuando los sensores del IES Simarro generen datos históricos suficientes.

La estrategia de datos adoptada sigue una **arquitectura Medallion**:
- **Capa bronce:** datasets públicos de referencia en su formato original.
- **Capa plata:** InfluxDB local con el schema canónico de CAPTIA (mismos buckets, measurement `captia_point`, 5 tags, field `value`), alimentado mediante ETL desde la capa bronce.
- **Capa oro:** artefactos específicos de cada caso de uso (features ML, embeddings, modelos entrenados, indicadores de calidad).

**La pregunta que os hacemos:** ¿podéis proporcionar un dump de InfluxDB con datos sintéticos o anonimizados de otra instalación, suficientemente ricos para que los equipos puedan entrenar y validar sus modelos? Y si no, o complementariamente, ¿podéis ayudarnos a que generemos esos datos sintéticos nosotros mismos?

---

## 2. Casos de uso del proyecto y datos que necesitan

A continuación se describen los once casos de uso con la información relevante para que podáis evaluar qué podéis aportarnos.

---

### Caso A — Pipeline IoT: simulación del flujo CENTINELA+

**Propósito:** Simular exactamente el proceso que realiza CENTINELA+ con sensores reales: publicación MQTT con topic canónico → Mosquitto → Telegraf → InfluxDB. Este caso tiene un alto valor pedagógico y quedará documentado como referencia para cursos futuros.

**Datos necesarios:** No necesita datos históricos para su objetivo principal. Simulará la publicación de un dataset público a través del pipeline IoT.

**Relevancia para CAPTIA:** Este grupo entenderá y documentará en detalle el flujo técnico de CENTINELA+. Su documentación y código quedarán como material de referencia y podrían usarse para formar a nuevos centros que se incorporen a la red CENTINELA.

---

### Caso B — Predicción de consumo eléctrico a 24 horas

**Propósito:** Entrenar modelos de predicción de consumo eléctrico (SARIMA, XGBoost, LSTM) con horizonte de 24 horas. El modelo entrenado debe ser directamente reutilizable con los datos de `power_01` de AULA01 cuando estén disponibles.

**Variables necesarias (mínimo 6-12 meses de historia horaria):**
- `power_01` — consumo eléctrico por aula o por planta (kW, variable objetivo)
- `temperature_outdoor` — temperatura exterior (°C, predictor principal)
- `solar_irradiance` — radiación solar (W/m², predictor secundario)
- `occupancy` o `people_count` — ocupación (predictor)
- Variables de estado HVAC (`ac_state`, `fan_speed_XX_state`) — como variables de contexto

**Desafío para datos sintéticos:** los modelos de predicción de consumo necesitan series temporales con variabilidad real: ciclos diarios, ciclos semanales, diferencias entre períodos lectivos y vacaciones, y correlación real con temperatura exterior. Un dataset sintético sin esa variabilidad producirá modelos que no generalizarán bien. Si el dataset sintético incluye estas correlaciones básicas (consumo sube cuando sube la temperatura en verano, baja durante vacaciones), será útil.

**Datasets públicos alternativos que usamos como fallback:** BDG2 (53M registros de edificios educativos, horario, con meteorología sincronizada) y UCI Appliances Energy Prediction.

---

### Caso C — Detección de anomalías en sistemas HVAC

**Propósito:** Entrenar modelos de detección de fallos en subsistemas de climatización usando Isolation Forest y Autoencoders. El modelo debe ser capaz de distinguir funcionamiento normal de fallos reales.

**Variables necesarias:**
- Temperaturas de suministro y retorno de aire (`temperature_supply`, `temperature_return`)
- Temperatura exterior (`temperature_outdoor`)
- Estado y posición de válvulas (`valve_control`, `valve_state`)
- Velocidad y estado de ventiladores (`fan_speed_XX`, `fan_speed_XX_state`)
- Caudal de aire o indicadores de flujo
- **Fundamental: etiquetas de eventos de fallo** — períodos donde el sistema funcionó incorrectamente (avería de válvula, fallo de sensor, comportamiento anómalo del compresor, etc.)

**Desafío para datos sintéticos:** este es el caso de uso donde el dataset sintético tiene más riesgo de ser insuficiente. Los modelos de detección de anomalías aprenden el patrón de funcionamiento normal y detectan desviaciones. Si el dataset sintético solo contiene funcionamiento normal o tiene anomalías artificiales que no reflejan los fallos reales que ocurren en instalaciones CAPTIA, los modelos no funcionarán bien en producción.

**Pregunta específica a CAPTIA:** ¿habéis tenido en vuestras instalaciones eventos de fallo documentados (fecha, tipo de fallo, sistema afectado) que pudierais compartir de forma anonimizada? Aunque solo sean 3-5 eventos reales, servirían como referencia para diseñar el dataset sintético de forma realista.

**Dataset público de fallback:** LBNL FDD (6.8 GB, series temporales de 7 subsistemas HVAC con fallos etiquetados de forma científica).

---

### Caso D — Calidad del aire, confort interior y detección de ocupación

**Propósito:** Desarrollar modelos de detección de ocupación a partir de variables ambientales (sin sensores de presencia explícitos) y análisis del índice IAQ. El resultado debe ser directamente aplicable a AULA01.

**Variables necesarias (mínimo 1-3 meses de historia, resolución de 1 minuto):**
- `co2` — concentración de CO₂ (ppm) — predictor principal de ocupación
- `temperature-indoor` — temperatura interior (°C)
- `relative-humidity` — humedad relativa (%)
- `avg-sound-level` — nivel de ruido (dB)
- `luminosity` — luminosidad (lux)
- `occupancy` o `people_count` — etiqueta de ocupación verificada
- Horario lectivo (períodos de clase, recreos, vacaciones) como metadata temporal

**Este es el caso de uso más alineado con las variables reales de AULA01.** Un dataset sintético de otra instalación CAPTIA similar (aulas escolares, oficinas con horario regular) sería de alto valor.

**Dataset público de fallback:** In-Gauge/En-Gage (datos reales de aulas escolares con horario lectivo documentado).

---

### Caso E — Meteorología y predicción de generación solar

**Propósito:** Procesar datos ERA5 para la zona de Valencia/Xàtiva y desarrollar un modelo de predicción de generación fotovoltaica. Los datos meteorológicos servirán también como entrada a los modelos del Caso B y como base de conocimiento del chatbot (Caso H).

**Variables necesarias:** temperatura exterior, punto de rocío, radiación solar (GHI), precipitación, viento, presión.

**Datos de CAPTIA relevantes:** si tenéis datos de producción solar de alguna instalación con paneles fotovoltaicos (aunque sea de otro cliente, anonimizados), serían muy valiosos para validar el modelo de predicción FV.

**Dataset principal:** ERA5 (ECMWF, datos de reanálisis climático global).

---

### Caso F — MLOps y ciclo de vida de modelos

**Propósito:** Implementar la infraestructura MLOps del proyecto: JupyterHub, MLflow, lakeFS. Garantizar que todos los experimentos son reproducibles y trazables.

**Datos de CAPTIA relevantes:** ninguno específico. Este caso de uso gestiona la infraestructura, no los datos.

---

### Caso G — Calidad de datos con agentes especialistas

**Propósito:** Definir y aplicar reglas de calidad sobre las capas bronce, plata y oro de todos los equipos. Desarrollar agentes especialistas que auditen automáticamente la calidad de los datos y los modelos, incluyendo la evaluación del chatbot.

**Datos de CAPTIA relevantes para este caso:** los **issues de calidad reales documentados en simarro-prod** son material de trabajo directo para este equipo:
- H-1: `site_id` inconsistente entre buckets (`ies_simarro` vs `ies_carlos_iii`)
- H-2: `registry.yaml` documenta `centinela_ies_simarro` pero los datos usan `ies_simarro`
- H-3: datos de entorno `env=dev` mezclados con producción
- Issue #27: override `asset_id` del normalizer solo aplica a metadata, no a telemetry writes
- Issue #29: `influx bucket create --retention 0` aplica 720h por defecto, no infinita

---

### Caso H — Sistema RAG, Agentes de IA y Chatbot

**Propósito:** Desarrollar un chatbot con arquitectura RAG capaz de responder preguntas sobre datos meteorológicos históricos y sobre el estado del edificio. Integra modelos predictivos de los Casos B, C y E.

**Datos de CAPTIA relevantes:**
- Si se consiguen los tokens read-only de InfluxDB (simarro-prod), el agente de edificio puede responder sobre el estado real de AULA01 en la demo del 29 de mayo.
- El catálogo `captia_metadata` con las variables del edificio (nombres, unidades, rangos) enriquece las respuestas del chatbot.

---

### Caso I — Big Data: Benchmark Spark vs. Pandas

**Propósito:** Demostrar empíricamente las ventajas del procesamiento distribuido con Spark frente a pandas, usando el dataset BDG2 completo (53M+ registros) en el clúster Hadoop del ITI.

**Datos de CAPTIA relevantes:** ninguno directo. Este caso usa BDG2 (datos de edificios de todo el mundo a escala). El resultado del benchmark es una de las bases técnicas para la propuesta de colaboración con AVAMET.

---

### Caso J — Tráfico y Visión Artificial con YOLOv

**Propósito:** Captura periódica de imágenes de cámaras DGT, detección de vehículos con YOLOv, y construcción de una serie temporal de intensidad de tráfico correlacionada con variables meteorológicas.

**Datos de CAPTIA relevantes:** ninguno directo. Este caso no usa datos del edificio.

---

## 3. Lo que os pedimos

### 3.1 Opción A — Dataset sintético en InfluxDB (ideal)

La opción más útil para el proyecto sería que pudierais proporcionarnos un **dump de InfluxDB** con datos sintéticos o anonimizados de una instalación similar al IES Simarro (edificio educativo con aulas, climatización, sensores de CO₂ y temperatura), con el schema canónico de CAPTIA ya en producción.

**Características deseables del dataset:**
- Mínimo 6 meses de historia en `telemetry_1h`, preferiblemente 12 meses.
- Las variables mínimas necesarias para los casos B, C y D (ver secciones anteriores).
- Variabilidad real: ciclos diarios, semanales, estacionales, diferencias entre períodos lectivos y vacaciones.
- Al menos algunos eventos on-change documentados en `state_events` (arranques y paradas del HVAC, cambios de setpoint).
- Si es posible, algunos eventos de funcionamiento anómalo del HVAC (para el Caso C), aunque sean pocos.

**Formato de entrega deseado:** dump de InfluxDB restaurable con `influx restore`, o fichero de line protocol importable con `influx write`. Que cada equipo pueda restaurarlo en su instancia local con un comando.

**Plazo:** nos sería útil tenerlo disponible antes del 12 de mayo de 2026.

---

### 3.2 Opción B — Ayudarnos a generar datos sintéticos (muy valorada)

Si la opción A no es viable, o como complemento a ella, nos sería enormemente útil vuestra colaboración para **generar nosotros mismos los datos sintéticos**. Esto tiene además valor estratégico para el proyecto a largo plazo: si en el futuro necesitamos ampliar el dataset (en este curso o en el próximo), podríamos hacerlo de forma autónoma sin molestaros.

**Lo que nos ayudaríais a entender:**

**3.2.1 Caracterización de variables**

Para cada variable del catálogo de CENTINELA+, necesitamos entender su comportamiento real para poder modelarlo sintéticamente de forma creíble. Concretamente:

| Variable | Información que necesitamos |
|----------|---------------------------|
| `co2` | Rango típico en horas lectivas vs. no lectivas. Velocidad de subida con X personas en el aula. Velocidad de bajada con ventilación. Valor base nocturno. |
| `temperature-indoor` | Rango de operación. Tiempo de respuesta al encender el HVAC. Correlación con temperatura exterior y con la hora del día. Diferencia entre invierno y verano. |
| `relative-humidity` | Rango típico por estación. Correlación con temperatura interior. |
| `power_01` | Perfil de consumo típico: arranque de mañana, horas de clase, horario de tarde. Diferencia entre días lectivos y festivos. Consumo base nocturno. |
| `ac_state` | Frecuencia media de arranques por día. Duración media de un ciclo de climatización. Correlación con setpoint y temperatura exterior. |
| `fan_speed_XX_state` | Distribución de velocidades durante un ciclo de climatización. |
| `luminosity` | Niveles típicos con luz natural vs. artificial. Correlación con hora del día y estación. |
| `avg-sound-level` | Niveles en horas de clase vs. recreo vs. horas vacías. |

**3.2.2 Patrones de correlación entre variables**

Los modelos ML aprenden correlaciones. Necesitamos entender cuáles son las correlaciones reales más importantes para modelarlas sintéticamente:
- ¿Cuánto sube la temperatura interior por grado de temperatura exterior en verano?
- ¿Cuántos ppm sube el CO₂ por persona y por minuto en un aula cerrada típica?
- ¿Cuánto cambia el consumo eléctrico cuando el HVAC pasa de velocidad baja a media?
- ¿Cuál es el tiempo de respuesta del CO₂ respecto al cambio de ocupación?

**3.2.3 Eventos de fallo y anomalías**

Para el Caso C (detección de anomalías HVAC), sería muy valioso que nos describierais los tipos de fallos más comunes que habéis observado en vuestras instalaciones:
- ¿Cuáles son los fallos más frecuentes en sistemas de climatización de centros educativos?
- ¿Cómo se manifiestan en los datos de los sensores? (por ejemplo: temperatura de suministro que no baja aunque el AC está encendido = posible fallo de compresor o refrigerante bajo)
- ¿Qué variables son los mejores indicadores de cada tipo de fallo?

No necesitamos datos de fallos reales (entendemos que pueden ser sensibles); nos basta con una descripción cualitativa del comportamiento esperado para poder diseñar escenarios sintéticos realistas.

---

### 3.3 Proceso propuesto para la generación sintética autónoma

Si nos proporcionáis la información de la sección 3.2, podríamos implementar un **generador de datos sintéticos reutilizable** que funcione así:

```python
# Ejemplo conceptual del generador
from synthetic_captia import CAPTIABuildingGenerator

gen = CAPTIABuildingGenerator(
    site_id="ies_simarro",
    asset_id="AULA01",
    school_calendar="valencian_2025_2026",
    occupancy_profile="secondary_school_50_students",
    climate_zone="valencia_koppen_Csa",
    hvac_type="fancoil_2pipe",
    # Parámetros que CAPTIA nos ayudaría a calibrar:
    co2_rise_rate_per_person_per_min=4.5,   # ppm/persona/minuto
    hvac_response_time_minutes=8,
    temp_outdoor_indoor_coupling=0.15,       # correlación T_ext -> T_int
)

df = gen.generate(
    start="2025-09-01",
    end="2026-06-30",
    resolution="1min",
    include_faults=True,
    fault_scenarios=["valve_stuck", "sensor_bias", "compressor_degraded"]
)

# Resultado: DataFrame con el schema CAPTIA listo para ingestar en InfluxDB
```

La clave es que los parámetros del generador queden calibrados con vuestra experiencia real. Una vez calibrados, el generador puede usarse en este curso, en el próximo y para cualquier instalación nueva.

---

## 4. Resumen de la solicitud

| Solicitud | Prioridad | Plazo deseado |
|-----------|-----------|--------------|
| Dump InfluxDB con datos sintéticos/anonimizados (6-12 meses, variables principales) | Alta | Antes del 12 mayo 2026 |
| Tokens read-only: `edu-token-simarro` (red LAN Simarro) | Alta | Antes del 9 mayo 2026 |
| Tokens read-only: `edu-token-iti` (red ITI / Tailscale) | Media | Antes del 9 mayo 2026 |
| Caracterización de variables (rangos, correlaciones, patrones) | Alta (para generación sintética) | Sin urgencia inmediata |
| Descripción de tipos de fallos HVAC observados (para Caso C) | Media | Sin urgencia inmediata |
| Validación del generador sintético que construiríamos nosotros | Media (curso siguiente) | Sin urgencia inmediata |

---

## 5. Por qué esto tiene valor más allá del proyecto actual

La colaboración que os pedimos tiene utilidad directa para CENTINELA+ más allá del proyecto de mayo:

1. **Generador de datos sintéticos calibrado:** una vez construido y validado con vuestra ayuda, podría usarse para entrenar los modelos que se desplegarán en CENTINELA+ antes de que los sensores del IES Simarro generen suficientes datos históricos. Esto acelera la puesta en producción de los modelos predictivos.

2. **Transferibilidad:** cuando CENTINELA+ se extienda a nuevos centros educativos, el generador permitirá crear datasets de arranque específicos para cada centro con sus características propias, sin esperar meses de datos reales.

3. **Validación de robustez:** los modelos entrenados con datos sintéticos bien calibrados pueden probarse contra escenarios de fallo que en datos reales tardarían meses en observarse.

4. **Documentación del comportamiento del sistema:** el proceso de calibrar el generador obliga a documentar con precisión el comportamiento esperado de cada variable en condiciones normales y anómalas — documentación que es valiosa por sí misma para el proyecto CENTINELA+.

---

Quedamos a vuestra disposición para cualquier aclaración y agradecemos de antemano vuestra colaboración con el proyecto.

Equipo docente IES Dr. Lluís Simarro — Curso de Especialización en IA y Big Data
