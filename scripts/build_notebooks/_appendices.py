"""Apéndices doctoral / corporativo precomputados por caso.

Cada caso define `APPENDICES` = lista de 3 tuplas (markdown, code) que se
añaden al final de cada notebook del caso:

- 19. Marco teórico (LaTeX MathJax).
- 20. Visión corporativa CAPTIA (propuesta de valor + ROI + riesgos).
- 21. Bibliografía.

Los textos resumen las secciones equivalentes de
``docs/use-cases/case-*.md`` para que el notebook sea autocontenido a
nivel docente.
"""

from __future__ import annotations

from scripts.build_notebooks._helpers import (
    bibliography_section,
    corporate_section,
    theory_section,
)


# ============================================================================
# Overview (00) — apéndices conceptuales sobre la arquitectura Medallion.
# ============================================================================

APPENDICES_OVERVIEW = [
    theory_section(
        r"""
### Arquitectura Medallion (Databricks 2021)

Tres capas con contratos de calidad incrementales:

$$
\mathcal{L}_b \xrightarrow{\text{ETL}_{b\to s}} \mathcal{L}_s \xrightarrow{\text{ETL}_{s\to o}} \mathcal{L}_o
$$

donde
$$
\mathcal{Q}(\mathcal{L}_o) > \mathcal{Q}(\mathcal{L}_s) > \mathcal{Q}(\mathcal{L}_b)
$$

con $\mathcal{Q}$ score de calidad ($\in [0, 1]$) según reglas del Caso G.

### Schema canónico CAPTIA

Modelo dimensional de **un único** measurement con 5 tags:

$$
\text{captia\_point}(\underbrace{e, d, s, a, v}_{5\ \text{tags}}, \underbrace{t}_{\text{ts\_ns}}, \underbrace{x}_{\text{value}})
$$

con cardinalidad efectiva
$$
|\mathcal{S}| = |E| \cdot |D| \cdot |S| \cdot |A| \cdot |V| \approx 3 \times 5 \times 10 \times 70 \times 24 = 252\,000
$$
series únicas como cota superior — en práctica decenas de miles.

### Reproducibilidad determinista

$$
\hat{y} = M(D, \theta, s = 42) \implies \text{hash}_2(\hat{y}_1) = \text{hash}_2(\hat{y}_2)
$$

con $s$ semilla, $D$ dataset (versionado lakeFS), $\theta$ hiperparámetros.
""",
    ),
    corporate_section(
        valor=(
            "**CAPTIA Technology** mantiene un schema canónico único en CENTINELA+. "
            "Este repo extiende ese schema a un **generador sintético reproducible** "
            "que permite:\n\n"
            "- Entrenar modelos de los casos B/C/D antes de tener histórico real "
            "del IES Simarro.\n"
            "- Onboarding de centros nuevos sin esperar meses de captura.\n"
            "- Datasets etiquetados de fallos HVAC para Caso C, normalmente "
            "imposibles de obtener.\n"
            "- Material docente alineado 1:1 con producción."
        ),
        roi_table_md=(
            "| Beneficio | Valor anual |\n"
            "|---|---|\n"
            "| Onboarding de 5 centros sin coste de captura | +25 000 € |\n"
            "| Material docente reutilizable curso a curso | +8 000 € |\n"
            "| Aceleración POC IA al cliente final | +12 000 € |\n"
            "| **Beneficio bruto** | **+45 000 €/año** |\n"
            "| Coste mantenimiento del repo | -3 000 €/año |\n"
            "| **Neto** | **+42 000 €/año** |"
        ),
        risks_md=(
            "- Calibración inicial sin datos reales del IES Simarro (mitigado con "
            "`docs/specs/digital-twin-bms-physics-validation/`).\n"
            "- Drift entre generador y producción: validado por suite 211/211 PASS "
            "y score realismo físico 0.94."
        ),
        baseline_section="Sec 1 (cartera total)",
    ),
    bibliography_section(
        [
            "Inmon, W. H., Linstedt, D., & Levins, M. (2019). *Data Architecture: A Primer for the Data Scientist*. Academic Press.",
            "Databricks (2021). *Lakehouse: A New Generation of Open Platforms*. CIDR.",
            "InfluxData (2024). *InfluxDB 2.7 Reference Architecture*. https://docs.influxdata.com/influxdb/v2/",
            "ECMWF (2024). *ERA5 reanalysis dataset documentation*. Copernicus Climate Change Service.",
        ]
    ),
]


# ============================================================================
# Caso A — Pipeline IoT CENTINELA+.
# ============================================================================

APPENDICES_CASE_A = [
    theory_section(
        r"""
### Modelo MQTT publicador-suscriptor (Banks et al. 2014)

Cada sensor emite un mensaje $m \in \mathcal{M}$ con QoS $q \in \{0, 1, 2\}$.
Para QoS 1 (at-least-once):

$$
P(\text{recibe} | q=1) \to 1 \quad \text{con} \quad P(\text{duplicado}) > 0
$$

Telegraf usa dedup por hash sobre `(asset_id, variable, ts_ns, value)` para
re-establecer exactly-once a nivel de InfluxDB.

### Throughput esperado

Si cada sensor publica a $f = 0.2$ Hz (cada 5 s) y hay $n = 70$ aulas con
$v = 22$ variables:

$$
\lambda = n \cdot v \cdot f = 70 \cdot 22 \cdot 0.2 = 308 \ \text{msg/s}
$$

Mosquitto soporta $> 10^4$ msg/s en hardware modesto, así que estamos lejos
del límite.

### Latencia end-to-end

$$
T_{e2e} = T_{sensor \to broker} + T_{telegraf} + T_{influx\_write} \lesssim 200\ \text{ms}
$$

con percentil 99 medido in-vivo $< 500$ ms.
""",
    ),
    corporate_section(
        valor=(
            "El pipeline IoT es la **infraestructura crítica** de CENTINELA+. "
            "Su disponibilidad determina la del producto entero. Este caso "
            "documenta y mide el flujo completo, da observabilidad (Prometheus + "
            "Loki + Grafana) y formaliza el contrato MQTT/Influx — base de "
            "cualquier despliegue en nuevos centros."
        ),
        roi_table_md=(
            "| Beneficio | Valor |\n"
            "|---|---|\n"
            "| Reducción tiempo onboarding nuevo centro (de 2 sem a 2 d) | +6 000 €/centro |\n"
            "| Detección temprana de fallos de ingesta | +3 000 €/año |\n"
            "| **Bruto** | **+9 000 €/año + 6 000 €/centro nuevo** |"
        ),
        risks_md=(
            "- ACL Mosquitto en dev: deshabilitar antes de producción.\n"
            "- Backpressure InfluxDB en picos > 1 000 msg/s: configurar buffer "
            "Telegraf de 60 s."
        ),
        baseline_section="Sec 2.1 (onboarding savings)",
    ),
    bibliography_section(
        [
            "Banks, A., Briggs, E., Borgendale, K. & Gupta, R. (2014). *MQTT Version 3.1.1*. OASIS.",
            "InfluxData (2024). *Telegraf 1.32 — MQTT Consumer Plugin*. https://docs.influxdata.com/telegraf/",
            "OASIS (2019). *MQTT v5.0*. https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html",
        ]
    ),
]


# ============================================================================
# Caso B — Forecast consumo eléctrico 24h.
# ============================================================================

APPENDICES_CASE_B = [
    theory_section(
        r"""
### Modelo SARIMA

$\text{SARIMA}(p,d,q)(P,D,Q)_s$ con período estacional $s$:

$$
\Phi_P(B^s)\,\phi_p(B)\,(1-B)^d\,(1-B^s)^D\,y_t = \Theta_Q(B^s)\,\theta_q(B)\,\varepsilon_t
$$

con $B$ operador retardo, $\varepsilon_t \sim \mathcal{N}(0, \sigma^2)$. Para
Simarro elegimos $s=24$ y $(p,d,q)(P,D,Q)_{24} = (2,0,2)(1,1,1)_{24}$ tras
minimizar AIC sobre BDG2.

### XGBoost regularizado (Chen & Guestrin 2016)

$$
\hat{y}_t = \sum_{k=1}^{K} f_k(\mathbf{x}_t), \quad f_k \in \mathcal{F}
$$

con función objetivo

$$
\mathcal{L}(\phi) = \sum_t \ell(y_t, \hat{y}_t) + \sum_k \Omega(f_k), \quad \Omega(f) = \gamma T + \tfrac{1}{2}\lambda \|w\|_2^2
$$

### LSTM (Hochreiter & Schmidhuber 1997)

$$
\begin{aligned}
f_t &= \sigma(W_f [h_{t-1}, x_t] + b_f) \\
i_t &= \sigma(W_i [h_{t-1}, x_t] + b_i) \\
\tilde{c}_t &= \tanh(W_c [h_{t-1}, x_t] + b_c) \\
c_t &= f_t \odot c_{t-1} + i_t \odot \tilde{c}_t \\
o_t &= \sigma(W_o [h_{t-1}, x_t] + b_o) \\
h_t &= o_t \odot \tanh(c_t)
\end{aligned}
$$

### Métricas

$$
\text{MAE} = \tfrac{1}{n}\sum |y_t - \hat{y}_t|, \quad
\text{sMAPE} = \tfrac{100\%}{n}\sum \frac{|y_t-\hat{y}_t|}{(|y_t|+|\hat{y}_t|)/2}
$$

Objetivos Simarro: $\text{MAE} \leq 0.15$ kWh, $\text{sMAPE} \leq 12\%$.
""",
    ),
    corporate_section(
        valor=(
            "Predicción de consumo a 24 h **habilita** ajuste anticipado de "
            "setpoints HVAC y compras de energía en franjas valle. Para CAPTIA es "
            "el caso con ROI más medible y más fácil de presentar a un cliente "
            "final. El modelo entrenado aquí es **directamente reutilizable** con "
            "los datos de `power_01` de cualquier centro CENTINELA+."
        ),
        roi_table_md=(
            "| Métrica | Valor |\n"
            "|---|---|\n"
            "| Ahorro consumo HVAC tras forecast + setpoint | ~15 % |\n"
            "| Aulas tipo Simarro (40) | 9 600 kWh / aula·año |\n"
            "| Coste energía España 2025 | 0.14 €/kWh |\n"
            "| **Ahorro centro:** $40 \\cdot 9\\,600 \\cdot 0.14 \\cdot 0.15$ | **8 064 €/año** |\n"
            "| Coste implantación | ~3 000 € one-time |\n"
            "| **Payback** | **~5 meses** |"
        ),
        risks_md=(
            "- Modelo sintético sin calibrar con datos reales: validar tras "
            "primer mes de captura.\n"
            "- Drift estacional: re-entrenar trimestralmente."
        ),
        baseline_section="Sec 2.2 (ahorro consumo HVAC)",
    ),
    bibliography_section(
        [
            "Box, G. E. P., Jenkins, G. M., Reinsel, G. C. & Ljung, G. M. (2015). *Time Series Analysis: Forecasting and Control* (5ª ed.). Wiley.",
            "Chen, T. & Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System*. KDD '16.",
            "Hochreiter, S. & Schmidhuber, J. (1997). *Long Short-Term Memory*. Neural Computation 9(8).",
            "Miller, C. et al. (2020). *The Building Data Genome 2 (BDG2) data-set*. Scientific Data.",
            "ASHRAE (2022). *ASHRAE 90.1-2022 — Energy Standard for Buildings*.",
        ]
    ),
]


# ============================================================================
# Caso C — Detección de anomalías HVAC.
# ============================================================================

APPENDICES_CASE_C = [
    theory_section(
        r"""
### Isolation Forest (Liu et al. 2008)

Score basado en la profundidad media $E[h(x)]$ del path al aislar $x$ en
árboles binarios construidos por particiones aleatorias:

$$
s(x, n) = 2^{-\frac{E[h(x)]}{c(n)}}
$$

con $c(n) = 2 H(n-1) - 2(n-1)/n$ y $H(i)$ harmonic number. Anomalía si
$s(x) \to 1$, normal si $s(x) \to 0.5$.

### Autoencoder (Hinton & Salakhutdinov 2006)

$$
\hat{x} = D(E(x)), \quad E: \mathbb{R}^d \to \mathbb{R}^k, \quad D: \mathbb{R}^k \to \mathbb{R}^d, \quad k \ll d
$$

con $k = 8$ neuronas en bottleneck para $d = 24$ features. Score:

$$
e(x) = \| x - \hat{x} \|_2^2, \quad \theta = \mu_e + 3\sigma_e
$$

### Catálogo de fallos (ADR-010)

| Tipo | Variable afectada | Signature |
|---|---|---|
| `sensor_drift` | `temperature_01` | drift lineal $+0.5$ °C/h |
| `valve_stuck` | `valve_state`, $T_{int}$ | $\Delta T \to 0$ tras setpoint change |
| `fan_failure` | `fan_speed_01_state`, $T_{supply}$ | $\dot V \to 0$, $T_{supply} \to T_{coil}$ |
| `refrigerant_low` | $T_{supply} - T_{return}$ | $\Delta T_{cool}$ cae 50 % |

### Métricas

$$
\text{F1} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}, \quad
\text{TPR}@1\%\text{FPR} = \text{Recall} \mid \text{FPR} \leq 0.01
$$

Objetivos: $\text{F1} \geq 0.85$, $\text{TPR}@1\%\text{FPR} \geq 0.7$.
""",
    ),
    corporate_section(
        valor=(
            "Detectar fallos HVAC antes de que se manifiesten en quejas de "
            "alumnos o averías catastróficas tiene **doble valor**: ahorro "
            "operativo (mantenimiento predictivo en lugar de reactivo) y "
            "diferenciador comercial frente a competidores BMS sin IA."
        ),
        roi_table_md=(
            "| Concepto | Valor anual |\n"
            "|---|---|\n"
            "| Detección temprana avería catastrófica (~2/año × 3 500 €) | +7 000 € |\n"
            "| Reducción downtime (2 h × 200 días) | +800 € |\n"
            "| **Bruto** | **+7 800 €/año** |\n"
            "| Coste integración | -2 000 € one-time |\n"
            "| **Payback** | **~3 meses** |"
        ),
        risks_md=(
            "- False positives → fatiga de alarmas. Tunear umbral con percentil 99.\n"
            "- Drift en HVAC envejecido: incluir age-feature."
        ),
        baseline_section="Sec 2.4 (incident reduction HVAC)",
    ),
    bibliography_section(
        [
            "Liu, F. T., Ting, K. M. & Zhou, Z.-H. (2008). *Isolation Forest*. ICDM '08.",
            "Hinton, G. & Salakhutdinov, R. (2006). *Reducing the Dimensionality of Data with Neural Networks*. Science 313(5786).",
            "Granderson, J. et al. (2020). *Building Fault Detection Data to Aid Diagnostic Algorithm Creation and Performance Testing*. Scientific Data 7.",
            "ASHRAE (2021). *Guideline 36-2021 — High-Performance Sequences of Operation for HVAC Systems*.",
        ]
    ),
]


# ============================================================================
# Caso D — Calidad aire e inferencia de ocupación.
# ============================================================================

APPENDICES_CASE_D = [
    theory_section(
        r"""
### Inferencia ocupación desde CO₂ (Wang et al. 2017)

Asumiendo balance de masa en aula bien mezclada:

$$
V \frac{dC(t)}{dt} = G \cdot N(t) - \dot V_{vent}(C(t) - C_{out})
$$

con $V$ volumen aula, $C$ concentración CO₂, $G$ generación per cápita
(~ $4.5 \times 10^{-3}$ L/s/persona ASHRAE 62.1), $N(t)$ ocupación,
$\dot V_{vent}$ caudal de ventilación.

Inversión: dada $C(t)$, $\dot V_{vent}$ conocida y $C_{out}$ medida,

$$
\hat{N}(t) = \frac{V \tfrac{dC}{dt} + \dot V_{vent}(C(t) - C_{out})}{G}
$$

### Random Forest para clasificación binaria

$$
\hat{y}(x) = \text{mode}\{T_b(x)\}_{b=1}^{B}, \quad T_b \sim \text{tree}(\mathcal{D}_b, \mathcal{F}_b)
$$

con bootstrap $\mathcal{D}_b$ y subconjunto features $\mathcal{F}_b$.

### Indicador IAQ unificado

$$
\text{IAQ} = w_1 \cdot \text{CO}_2 + w_2 \cdot t\text{VOC} + w_3 \cdot \text{HR} + w_4 \cdot T_{int}
$$

con pesos calibrados para reflejar normativa EN 16798.
""",
    ),
    corporate_section(
        valor=(
            "Inferir ocupación sin sensores de presencia explícitos **abarata** el "
            "BOM de cada aula instrumentada por CAPTIA. El indicador IAQ "
            "consolidado simplifica la comunicación con dirección de centro."
        ),
        roi_table_md=(
            "| Concepto | Valor |\n"
            "|---|---|\n"
            "| Ahorro BOM por aula (sin sensor presencia) | -45 €/aula |\n"
            "| 70 aulas Simarro × 45 € | **+3 150 € one-time** |\n"
            "| Reducción quejas calidad aire | +2 000 €/año |\n"
            "| **Total año 1** | **+5 150 €** |"
        ),
        baseline_section="Sec 2.2 (alertas IAQ)",
    ),
    bibliography_section(
        [
            "ASHRAE (2022). *Standard 62.1-2022 — Ventilation for Acceptable Indoor Air Quality*.",
            "EN 16798-1:2019. *Energy performance of buildings — Ventilation for buildings*.",
            "Wang, S., Burnett, J. & Chong, H. (2017). *Experimental validation of CO₂-based demand-controlled ventilation*. Building and Environment 39(2).",
            "OMS (2010). *WHO Guidelines for Indoor Air Quality*.",
        ]
    ),
]


# ============================================================================
# Caso E — Meteorología y predicción solar.
# ============================================================================

APPENDICES_CASE_E = [
    theory_section(
        r"""
### Modelo de irradiancia solar global (Iqbal 1983)

$$
G_h(t) = G_b(t) + G_d(t), \quad G_b(t) = G_{sc} \cdot \tau_b(t) \cdot \cos\theta_z(t)
$$

con $G_{sc} = 1361$ W/m² constante solar y $\theta_z$ ángulo cenital del sol:

$$
\cos\theta_z = \sin\delta \sin\phi + \cos\delta \cos\phi \cos\omega
$$

donde $\delta$ es declinación solar, $\phi$ latitud (Xátiva 38.99°N) y
$\omega$ ángulo horario.

### Clear-sky index

$$
k_c(t) = \frac{G_h(t)}{G_{clear}(t)} \in [0, 1]
$$

separa astronomía (determinista) de meteorología (estocástica).

### Predictor XGBoost para FV

$$
\hat{P}(t+h) = P_{nominal} \cdot \eta_{panel} \cdot \text{XGB}(k_c(t), T_{out}, t_{hora}, t_{año})
$$

### Métrica Skill Score

$$
\text{Skill} = 1 - \frac{\text{RMSE}_{model}}{\text{RMSE}_{persistence}}
$$

Objetivo Simarro: $\text{nMAE} \leq 8\%$ a 24 h, $\text{Skill} \geq 0.3$.
""",
    ),
    corporate_section(
        valor=(
            "Predicción solar permite optimizar despacho energético en centros con "
            "FV instalada y planificar climatización aprovechando picos de "
            "radiación. CAPTIA puede ofrecer este caso como **producto añadido** a "
            "centros con paneles."
        ),
        roi_table_md=(
            "| Concepto | Valor |\n"
            "|---|---|\n"
            "| Optimización despacho FV (centro 50 kWp) | +800 €/año |\n"
            "| Sinergia con Caso B forecast | +500 €/año |\n"
            "| Coste integración ERA5+AEMET | -1 200 € one-time |\n"
            "| **Payback** | **~12 meses** |"
        ),
        baseline_section="Sec 3 (PV system)",
    ),
    bibliography_section(
        [
            "Iqbal, M. (1983). *An Introduction to Solar Radiation*. Academic Press.",
            "ECMWF (2024). *ERA5 Reanalysis Documentation*. Copernicus Climate Change Service.",
            "AEMET. *Open Data Portal*. https://opendata.aemet.es",
            "Holmgren, W. F. et al. (2018). *pvlib python: a python package for modeling solar energy systems*. JOSS 3(29).",
        ]
    ),
]


# ============================================================================
# Caso F — MLOps y reproducibilidad.
# ============================================================================

APPENDICES_CASE_F = [
    theory_section(
        r"""
### Versionado de datasets (lakeFS)

Modelo Git-like sobre object storage con commits inmutables:

$$
\text{commit}_t = \langle \text{tree}_t, \text{parent}_{t-1}, \text{metadata}_t \rangle
$$

con `tree` Merkle DAG. Modelos referencian
$\text{dataset\_uri} = \text{lakefs://repo/branch/commit\_id}$ no paths mutables.

### MLflow Run Schema

$$
\text{run}_i = \langle \text{params}_i, \text{metrics}_i, \text{artifacts}_i, \text{tags}_i, \text{dataset\_uri}_i \rangle
$$

### Reproducibilidad determinista

$$
\hat{y} = M(D, \theta, s = 42), \quad
\text{hash}(\hat{y}_1) = \text{hash}(\hat{y}_2) \iff (D_1, \theta_1, s_1) = (D_2, \theta_2, s_2)
$$

(ADR-008). Verificable con `pytest -m snapshot`.

### Linaje de features

$$
\text{Feature}_i = f_i(\text{Feature}_j, \text{Feature}_k, ...) \implies \text{DAG}_{features}
$$

Trazabilidad bidireccional dataset $\leftrightarrow$ run $\leftrightarrow$ deploy.
""",
    ),
    corporate_section(
        valor=(
            "MLOps no genera ROI directo, pero **reduce el coste de toda la "
            "cadena**. Permite a CAPTIA mover modelos a producción con "
            "confianza, hacer auditorías regulatorias (próxima EU AI Act) y "
            "evitar el clásico *funcionaba en mi máquina*."
        ),
        roi_table_md=(
            "| Concepto | Valor |\n"
            "|---|---|\n"
            "| Reducción tiempo auditoría modelos (8 h → 1 h) | +800 €/año |\n"
            "| Eliminación re-runs por incertidumbre | +400 €/año compute |\n"
            "| Cumplimiento EU AI Act (riesgo evitado) | +20 000 € (riesgo) |\n"
            "| **Bruto** | **+1 200 €/año** + risk hedging |"
        ),
        baseline_section="Sec 4 (compliance EU AI Act)",
    ),
    bibliography_section(
        [
            "Zaharia, M. et al. (2018). *Accelerating the Machine Learning Lifecycle with MLflow*. CIDR.",
            "lakeFS Project. *Documentation*. https://docs.lakefs.io",
            "Sculley, D. et al. (2015). *Hidden Technical Debt in Machine Learning Systems*. NeurIPS.",
            "EU (2024). *Artificial Intelligence Act*. Regulation (EU) 2024/1689.",
        ]
    ),
]


# ============================================================================
# Caso G — Calidad de datos con agentes.
# ============================================================================

APPENDICES_CASE_G = [
    theory_section(
        r"""
### Reglas de calidad jerárquicas

Sea $\mathcal{D}_b$ bronce, $\mathcal{D}_s$ plata, $\mathcal{D}_o$ oro.
Score por capa:

$$
\mathcal{Q}(\mathcal{D}) = \frac{1}{|R|} \sum_{r \in R} \mathbb{1}[E_r(\mathcal{D})\ \text{holds}], \quad \mathcal{Q} \in [0, 1]
$$

| Capa | Reglas |
|---|---|
| Bronce | Schema validity, no PII inline, encoding UTF-8, dedup |
| Plata | 5 tags canónicos, range check, monotonic time, NaN < 2 % |
| Oro | Class balance, no leakage, splits documented |

### Drift detection — KL divergence

$$
D_{KL}(P \parallel Q) = \sum_x P(x) \log \frac{P(x)}{Q(x)}
$$

aplicado entre histogramas $P$ (training) y $Q$ (production). Alerta si
$D_{KL} > 0.1$.

### Agentes especialistas (LLM con tools)

$$
\text{Agent}_i = \langle \pi_i, \mathcal{T}_i, \mathcal{M}_i \rangle
$$

con $\pi_i$ política (prompt), $\mathcal{T}_i$ toolkit, $\mathcal{M}_i$
memoria. Composición vía pipeline:

$$
\text{Output} = \pi_n(\pi_{n-1}(\cdots \pi_1(\text{Input})))
$$
""",
    ),
    corporate_section(
        valor=(
            "Calidad de datos es **transversal**: sin ella ningún caso de uso "
            "tiene valor. Los agentes especialistas automatizan auditorías que "
            "antes requerían un data engineer dedicado."
        ),
        roi_table_md=(
            "| Concepto | Valor |\n"
            "|---|---|\n"
            "| Detección temprana de drift en modelos | +1 500 €/año |\n"
            "| Auditoría continua sin intervención | +800 €/año productividad |\n"
            "| **Bruto** | **+2 300 €/año** |"
        ),
        baseline_section="Sec 2.2 (incident reduction)",
    ),
    bibliography_section(
        [
            "Schelter, S. et al. (2018). *Automating Large-Scale Data Quality Verification*. VLDB.",
            "Great Expectations. *Documentation*. https://greatexpectations.io",
            "Anthropic (2024). *Claude API — Tools*. https://docs.anthropic.com",
            "Polyzotis, N. et al. (2017). *Data Lifecycle Challenges in Production Machine Learning*. SIGMOD.",
        ]
    ),
]


# ============================================================================
# Caso H — RAG + Chatbot.
# ============================================================================

APPENDICES_CASE_H = [
    theory_section(
        r"""
### Retrieval-Augmented Generation (Lewis et al. 2020)

$$
P(y \mid x) = \sum_{z \in \mathcal{Z}} P_\eta(z \mid x) \cdot P_\theta(y \mid x, z)
$$

con $x$ pregunta, $z$ documento recuperado, $P_\eta$ retriever (cosine sobre
embeddings) y $P_\theta$ LLM generador.

### Similarity coseno

$$
\text{sim}(x, z) = \frac{\mathbf{e}_x \cdot \mathbf{e}_z}{\|\mathbf{e}_x\| \|\mathbf{e}_z\|}
$$

### Tools tipadas

$$
\mathcal{T} = \{ t_i : \mathbb{X}_i \to \mathbb{Y}_i \mid \text{schema JSON} \}
$$

Cada tool publica su firma en formato JSON Schema; el LLM la consume vía
function-calling.

### Métricas

$$
\text{Hit Rate@k} = \tfrac{1}{N} \sum_i \mathbb{1}[\text{rank}_i \leq k], \quad
\text{MRR} = \tfrac{1}{N} \sum_i \tfrac{1}{\text{rank}_i}
$$

Objetivos: $\text{Hit@5} \geq 0.85$, $\text{MRR} \geq 0.7$, Faithfulness ≥ 0.9.
""",
    ),
    corporate_section(
        valor=(
            "El chatbot es la **cara visible** de CAPTIA al usuario final "
            "(profesores, equipo de mantenimiento). Una sola interfaz unifica "
            "métricas históricas, predicciones y conocimiento documental, "
            "reduciendo drásticamente la necesidad de soporte L1."
        ),
        roi_table_md=(
            "| Concepto | Valor |\n"
            "|---|---|\n"
            "| Reducción tickets soporte L1 | +3 500 €/año |\n"
            "| Tiempo respuesta profesores | +1 200 €/año |\n"
            "| **Bruto** | **+4 700 €/año** |\n"
            "| Coste API LLM (Claude/GPT) | -1 800 €/año |\n"
            "| **Neto** | **+2 900 €/año** |"
        ),
        risks_md=(
            "- Hallucinations del LLM: mitigar con tools de hechos verificables.\n"
            "- Coste API escala linealmente con uso: monitorizar."
        ),
        baseline_section="Sec 2.2 (automation L1)",
    ),
    bibliography_section(
        [
            "Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS.",
            "Reimers, N. & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. EMNLP.",
            "LangChain Project. *Documentation*. https://python.langchain.com",
            "Anthropic (2024). *Claude 3.5 Sonnet Model Card*.",
        ]
    ),
]


# ============================================================================
# Caso I — Spark vs Pandas.
# ============================================================================

APPENDICES_CASE_I = [
    theory_section(
        r"""
### Modelo de coste pandas (single-node)

$$
T_{pandas}(N) = O(N) \quad \text{si} \quad N \cdot d \cdot 8 \text{ bytes} \leq \text{RAM}
$$

con OOM cuando se supera la RAM disponible.

### Modelo de coste Spark (distribuido)

$$
T_{Spark}(N, p) = T_{startup} + \frac{N}{p} \cdot t_{cpu} + O(\log p) \cdot t_{shuffle}
$$

con $p$ paralelismo, $t_{shuffle}$ coste red por partición.

### Punto de cruce

$$
N^* = \frac{T_{startup} \cdot p}{t_{cpu}^{pandas} - t_{cpu}^{spark}}
$$

A escala $N \gtrsim 10^7$ filas con ops shuffle-heavy, Spark domina; por
debajo, pandas es más rápido.

### Benchmark BDG2 (53M filas)

| Operación | pandas | Spark p=4 | Spark p=16 |
|---|---|---|---|
| Read CSV | ~120 s | ~45 s | ~18 s |
| GroupBy | ~25 s | ~30 s | ~12 s |
| Join | ~80 s OOM | ~35 s | ~14 s |
| **Total ETL** | **~285 s** | **~160 s** | **~66 s** |
""",
    ),
    corporate_section(
        valor=(
            "Decidir cuándo escalar a Spark **ahorra dinero**: ejecutar pandas "
            "sobre un VM grande es a veces más barato que un cluster Spark. "
            "Este caso da la regla práctica para el equipo de operaciones."
        ),
        roi_table_md=(
            "| Concepto | Valor |\n"
            "|---|---|\n"
            "| Reducción ETL diario 50 % | +800 €/mes cloud |\n"
            "| **Bruto** | **+9 600 €/año** |\n"
            "| Setup Spark on K8s | -2 500 € one-time |\n"
            "| **Payback** | **~3 meses** |"
        ),
        baseline_section="Sec 3 caso I (Spark TCO)",
    ),
    bibliography_section(
        [
            "Zaharia, M. et al. (2010). *Spark: Cluster Computing with Working Sets*. HotCloud.",
            "Miller, C. et al. (2020). *The Building Data Genome 2 (BDG2) data-set*. Scientific Data 7.",
            "Dean, J. & Ghemawat, S. (2008). *MapReduce: Simplified Data Processing on Large Clusters*. CACM 51(1).",
        ]
    ),
]


# ============================================================================
# Caso J — Tráfico + YOLO.
# ============================================================================

APPENDICES_CASE_J = [
    theory_section(
        r"""
### YOLO v8 — single-stage anchor-free detector

Por cada celda de la grid, salida:

$$
\hat{y} = (b_x, b_y, b_w, b_h, p_{obj}, p_{c_1}, ..., p_{c_C})
$$

Loss combinada:

$$
\mathcal{L} = \lambda_{box} \mathcal{L}_{CIoU} + \lambda_{obj} \mathcal{L}_{BCE,obj} + \lambda_{cls} \mathcal{L}_{BCE,cls}
$$

### Series temporales tráfico

$$
N_v(t) = \sum_{i=1}^{D_t} \mathbb{1}[\text{detection}_i \in v_{ROI}]
$$

con NMS IoU threshold = 0.5.

### Predictor congestión

$$
\hat{C}(t+15) = \text{XGB}(N_v(t), N_v(t-15), ..., \text{weather}, t_{hora}, t_{dow})
$$

con $C \in \{0, 1, 2, 3\}$ niveles de congestión.

### Métricas

$$
\text{mAP}@0.5 = \frac{1}{|C|} \sum_{c \in C} \text{AP}_c \quad (\text{IoU} \geq 0.5)
$$

Objetivos: mAP@0.5 ≥ 0.90 (car/truck), ≥ 0.75 (motorbike/bicycle).
""",
    ),
    corporate_section(
        valor=(
            "Aunque tangencial al BMS de aulas, este caso demuestra que la "
            "**stack de IA + datos sintéticos + modelos** de CAPTIA es "
            "extensible a otros verticales (smart cities). Activo comercial "
            "para diversificar."
        ),
        roi_table_md=(
            "| Concepto | Valor |\n"
            "|---|---|\n"
            "| Predicción congestión 15 min (semáforos) | +5 000 €/año |\n"
            "| Detección incidentes < 60 s (emergencias) | +12 000 €/año |\n"
            "| **Bruto** | **+17 000 €/año** |\n"
            "| Compute GPU dedicada | -1 500 €/año |\n"
            "| **Neto** | **+15 500 €/año** |"
        ),
        baseline_section="Sec 3 caso J (smart cities)",
    ),
    bibliography_section(
        [
            "Redmon, J. & Farhadi, A. (2018). *YOLOv3: An Incremental Improvement*. arXiv:1804.02767.",
            "Ultralytics (2024). *YOLOv8 Documentation*. https://docs.ultralytics.com",
            "Lin, T.-Y. et al. (2014). *Microsoft COCO: Common Objects in Context*. ECCV.",
            "DGT España. *Información en tiempo real*. http://infocar.dgt.es",
        ]
    ),
]
