"""Helpers compartidos por los módulos de cada caso."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from scripts._nb_builder import SETUP_BLOCK, header, write_notebook


# Notas etapa-específicas (genéricas, fallback). Usadas si no hay entrada
# en _CASE_STAGE_NOTES más específica.
_STAGE_NOTES = {
    "01": (
        "EDA — exploración de datos crudos",
        "Esta etapa es **exploración**, no modelado. Buen EDA evita 80 % "
        "de los errores ML downstream — invertir tiempo aquí ahorra bugs caros.",
    ),
    "02": (
        "ETL bronce → plata",
        "Esta etapa cristaliza el contrato `captia_point` + 5 tags + `value`. "
        "Cada vendor nuevo reusa este patrón (~3 600 €/año ahorrado en integración, "
        "ver `docs/captia/economic_baseline.md` §2.3).",
    ),
    "03": (
        "Feature engineering oro",
        "Las features son **el activo reusable** de mayor ROI: una feature "
        "validada (ej. `dCO2/dt`) sirve a todos los modelos del caso y entre casos.",
    ),
    "04": (
        "Modelado y baselines",
        "**No modelo sin baseline**. Sin la comparación naïve / regla / climatología, "
        "ningún MAE / F1 reportado es defendible ante un comité técnico.",
    ),
    "05": (
        "Validación y operación",
        "Esta etapa cierra el ciclo: rigor estadístico (IC bootstrap, walk-forward) "
        "+ KPIs operacionales (alertas/día, MTTR). Sin ella el modelo no llega a producción.",
    ),
}


# Notas específicas por (carpeta_caso, prefijo_notebook). Cada par produce
# un párrafo **único** anclado al dominio Simarro/AULA01/CENTINELA+. Esto
# elimina la duplicación NA-A: los 5 notebooks de un caso ya no comparten
# el mismo apéndice 22 — cada uno habla de su etapa concreta.
_CASE_STAGE_NOTES: dict[tuple[str, str], tuple[str, str]] = {
    # Overview (3 notebooks)
    ("00_project_overview", "00"): (
        "Mapa Medallion — bronce/plata/oro aplicado a CENTINELA+",
        "Punto de entrada: 11 casos × 4 capas Medallion. CAPTIA ya resolvió internamente "
        "el bronce → plata para `simarro-prod`; los notebooks reproducen ese contrato y "
        "construyen oros específicos por caso.",
    ),
    ("00_project_overview", "01"): (
        "Schema canónico CAPTIA — measurement, tags, field, buckets",
        "Los 5 tags + field `value` + measurement único `captia_point` constituyen el "
        "**contrato inmutable** sobre el que pivotan los 45 notebooks. Cualquier ETL "
        "BMS produce líneas que pasan por este schema.",
    ),
    ("00_project_overview", "02"): (
        "Conexión `.env` → InfluxDB con fallback offline",
        "El alumno aprende **antes de tocar datos** la disciplina de no hardcodear "
        "secretos. Usa `python-dotenv` + `INFLUX_OFFLINE=true` para clase sin stack.",
    ),
    # Caso A — Pipeline IoT (3 notebooks)
    ("01_case_A_pipeline_iot", "01"): (
        "Diagnosis del pipeline CENTINELA+",
        "El alumno entiende **cómo se mueve un dato** del sensor a Grafana antes de "
        "intentar publicar. AULA01 publica 22 variables × 0.2 Hz = 4.4 msg/s; "
        "70 aulas extrapoladas = 308 msg/s — Mosquitto soporta 10⁴ msg/s. "
        "Ver `docs/architecture/data-flow.md`.",
    ),
    ("01_case_A_pipeline_iot", "02"): (
        "Publicación MQTT real con paho-mqtt + fallback in-memory",
        "Punto crítico: medir el **throughput real** publicación vs el "
        "λ teórico de CENTINELA+ (308 msg/s). Si el cliente tarda > 100 ms/msg "
        "en lab, en producción colapsará durante el turno mañana de las 25 aulas.",
    ),
    ("01_case_A_pipeline_iot", "03"): (
        "Validación schema canónico tras Telegraf",
        "Comprobar los 5 tags + `value` en `captia_point` es la **única forma** de "
        "detectar regex Telegraf rotas antes de que afecten al dashboard de "
        "AULA01 que el director del IES revisa cada lunes.",
    ),
    # Caso B — Forecast consumo
    ("02_case_B_energy_forecasting", "01"): (
        "EDA consumo eléctrico AULA01 / BDG2",
        "ADF + ACF revelan que `power_kw` es **no estacionaria** sin diferenciación 24h "
        "y la ACF muestra picos en lag-24 y lag-168 → **SARIMA(p,d,q)(P,D,Q)_24** "
        "es la familia correcta. Sin este EDA, un alumno mete RandomForest "
        "directamente y nunca sabrá por qué falla en la franja de noche.",
    ),
    ("02_case_B_energy_forecasting", "02"): (
        "ETL BDG2 → captia_point con dominio bms_buildings",
        "BDG2 (53M filas reales) y AULA01 (datos sintéticos hoy, reales pronto) "
        "comparten el mismo schema. Cuando llegue `simarro-prod`, este ETL se "
        "reusa sin tocar 1 línea — solo cambia `domain_id=bms_classrooms`.",
    ),
    ("02_case_B_energy_forecasting", "03"): (
        "Features con calendario lectivo Comunidad Valenciana",
        "Las features `lag_24h`, `lag_168h`, `is_lectivo` capturan el patrón "
        "**escolar** de Simarro: pico mañana 08-15h, valle 22-08h, vacaciones "
        "Navidad/Fallas/Semana Santa/Verano. Un modelo sin `is_lectivo` predice "
        "consumo lectivo en agosto = error 80 %.",
    ),
    ("02_case_B_energy_forecasting", "04"): (
        "Modelado: SARIMA + XGBoost + naive_24h",
        "**3 baselines comparables con IC bootstrap** sobre los mismos features. "
        "Si XGBoost no bate naive_24h, el feature engineering es el problema, "
        "no el modelo. Para AULA01 con 1 año de histórico esperamos "
        "MAE ≤ 0.15 kWh y sMAPE ≤ 12 %.",
    ),
    ("02_case_B_energy_forecasting", "05"): (
        "Walk-forward 24h con re-entrenamiento diario",
        "Métricas por horizonte (1h, 6h, 12h, 24h): el error crece "
        "**linealmente** con el horizonte si el modelo es estable. Si crece "
        "exponencialmente → concept drift no detectado. Trigger de "
        "re-entrenamiento: MAE_improvement_pct < 0 durante 3 días seguidos.",
    ),
    # Caso C — Anomalías HVAC
    ("03_case_C_hvac_anomaly_detection", "01"): (
        "EDA LBNL FDD: 4 firmas físicas distinguibles",
        "`valve_stuck` → ΔT supply-return cae con AC encendido; `sensor_drift` → "
        "deriva lineal +0.5 °C/h; `fan_failure` → caudal CFM = 0; "
        "`refrigerant_low` → ΔT_cool cae 50 %. Cada firma es **un feature** "
        "para el modelo del notebook 04.",
    ),
    ("03_case_C_hvac_anomaly_detection", "02"): (
        "Etiquetas en captia_fault_labels (NO en captia_point)",
        "Separar etiquetas del telemetry permite entrenar IF/AE sin contaminar el "
        "schema. Un consumidor lee `from(bucket:state_events) "
        "|> filter(_measurement==captia_fault_labels)` para obtener tickets "
        "sin tocar la telemetría operativa.",
    ),
    ("03_case_C_hvac_anomaly_detection", "03"): (
        "Features ΔT, duty cycles, ratio fan/valve",
        "`dt_supply_return = T_return - T_supply` debería ser ≥ 6 °C en cooling "
        "operativo y ≈ 0 en valve_stuck. Esta única feature ya distingue "
        "valve_stuck con AUC ≈ 0.85 — IF/AE solo añaden +0.10.",
    ),
    ("03_case_C_hvac_anomaly_detection", "04"): (
        "Isolation Forest + Autoencoder con 4 baselines",
        "Comparación rigurosa: rule-based ΔT, z-score rolling, IF, AE solo-normales. "
        "**Sin baseline rule-based**, IF/AE parecen siempre buenos; con él, "
        "el alumno descubre que la regla física bate al ML el 70 % del tiempo.",
    ),
    ("03_case_C_hvac_anomaly_detection", "05"): (
        "Validación supervisada por tipo + matriz coste-sensible",
        "F1 macro engaña con desbalance de tipos. Recall por tipo (`valve_stuck` 0.9, "
        "`refrigerant_low` 0.7) muestra dónde el modelo necesita más datos. "
        "Coste FN(`refrigerant_low`) = 1 800 € (recarga + degradación COP).",
    ),
    # Caso D — IAQ + ocupación
    ("04_case_D_iaq_occupancy", "01"): (
        "EDA In-Gauge AULA01: CO₂ delata ocupación",
        "El balance de masa CO₂ (Wang 2017) predice "
        "$\\frac{dC}{dt} \\propto N(t)$. En el mock vemos que `dCO2/dt > +15 ppm/min` "
        "coincide con clase activa, valor base nocturno = 410 ppm.",
    ),
    ("04_case_D_iaq_occupancy", "02"): (
        "ETL In-Gauge → captia_point + captia_point_meta",
        "El catálogo `captia_point_meta` es **crítico**: sin él los rollups "
        "Telegraf no se generan y `telemetry_1h` queda vacío → el chatbot del "
        "Caso H devuelve 'sin datos' al profesor que pregunta 'temperatura "
        "ayer en AULA01'.",
    ),
    ("04_case_D_iaq_occupancy", "03"): (
        "Features dCO2/dt + IAQ index EN 16798",
        "`dCO2/dt(5min)` es la señal **predictiva clave** para inferir ocupación "
        "sin sensor de presencia. El IAQ index (CO₂ + tVOC + HR) alinea con "
        "categorías I/II/III/IV de la norma EN 16798 — ventaja competitiva en "
        "pliegos públicos del sector educativo.",
    ),
    ("04_case_D_iaq_occupancy", "04"): (
        "Inferencia ocupación: balance físico vs RandomForest",
        "**Patrón pedagógico oro**: comparar 3 modelos (threshold trivial / "
        "balance de masa analítico / RF balanceado) sobre 30 días con "
        "`TimeSeriesSplit(5)`. Demuestra que un modelo físico calibrado puede "
        "batir a un RF mal alimentado.",
    ),
    ("04_case_D_iaq_occupancy", "05"): (
        "Alertas IAQ con histéresis y jerarquía L1/L2/L3",
        "Sin histéresis, fatiga de alarmas → operador desactiva → producto "
        "invisible. Con histéresis 5 min sostenido + banda 75 ppm rearme: "
        "reducción del 80-95 % en alertas falsas. Coste evitado de "
        "'sistema desactivado' ≈ 1 050 €/año (baseline §2.2).",
    ),
    # Caso E — Meteo & solar
    ("05_case_E_weather_solar", "01"): (
        "EDA ERA5 Xàtiva: ciclo diurnal + estacional",
        "Diurnal de GHI con pico ≈ 12:00 hora local; ciclo anual con declinación "
        "δ = 23.45·sin(2π(doy+284)/365). Sin entender geometría solar, "
        "modelar GHI es como modelar mareas sin saber que la luna existe.",
    ),
    ("05_case_E_weather_solar", "02"): (
        "ETL ERA5 con conversiones K→°C, J/m²→W/m², m→mm",
        "ERA5 viene en SI nativo (K, J/m², m); CAPTIA opera en convención BMS "
        "(°C, W/m², mm). Una conversión olvidada genera GHI = 350 000 W/m² en "
        "Grafana — error visible inmediatamente, pero solo si el alumno mira.",
    ),
    ("05_case_E_weather_solar", "03"): (
        "Features dewpoint Magnus + clear-sky index",
        "El clear-sky index $k_c = G_h / G_{clear} \\in [0, 1]$ separa "
        "**astronomía determinista** de **meteorología estocástica**. Predecir "
        "$k_c$ con XGBoost es 5× más preciso que predecir GHI directamente.",
    ),
    ("05_case_E_weather_solar", "04"): (
        "Predicción solar: 4 baselines + skill score",
        "Climatología por hora bate al RF sobre 720 horas — lección dura: el "
        "modelo elaborado no siempre vence al baseline simple. Para Simarro "
        "esto significa: **antes de invertir en GPU, prueba climatología**.",
    ),
    # Caso F — MLOps
    ("06_case_F_mlops", "01"): (
        "MLflow hello-world + naming convention CAPTIA",
        "Convención: `experiment_name = ^case_[A-J]_(baseline|prod)_\\d{4}$`. "
        "Sin convención, dos data scientists del IES Simarro registran "
        "`exp_test_2026` y `experimento_juan` — auditoría imposible al cabo de "
        "3 meses.",
    ),
    ("06_case_F_mlops", "02"): (
        "Tracking experimentos + lakeFS tag",
        "Cada run debe llevar `mlflow.set_tag('lakefs_tag', 'case_B/baseline_v1')`. "
        "El día que llegue una auditoría EU AI Act, el responsable necesita "
        "**reproducir** el modelo desplegado hace 6 meses sobre los datos "
        "exactos — sin tag lakeFS, irreproducible.",
    ),
    ("06_case_F_mlops", "03"): (
        "Reproducibilidad determinista (hash dataset + modelo)",
        "Mismo seed + mismos datos → bytes idénticos del modelo. "
        "BLAS no determinista en multi-thread es la trampa #1 — solución: "
        "`OMP_NUM_THREADS=1` en producción y aceptar 5-10 % de overhead "
        "compute a cambio de auditabilidad.",
    ),
    # Caso G — Calidad agentes
    ("07_case_G_data_quality_agents", "01"): (
        "Reglas calidad bronce sin dependencia de servicios",
        "Equipo G empieza la **Semana 1** sin esperar a que los demás carguen "
        "InfluxDB. Reglas sobre los CSV originales (BDG2, In-Gauge, LBNL FDD) "
        "ya detectan problemas antes del ETL.",
    ),
    ("07_case_G_data_quality_agents", "02"): (
        "Reglas Flux sobre la capa plata",
        "5 tags presentes + `value` único + completitud > 95 % por hora. "
        "Convertibles a Flux Tasks con notification a Slack #captia-alerts. "
        "Detectan caída de sensor en < 15 min vs 6 h en cambio de turno.",
    ),
    ("07_case_G_data_quality_agents", "03"): (
        "Calidad oro: KL divergence train vs prod",
        "KL ≥ 0 (Gibbs) — si reportas KL negativo, hay un bug en tu "
        "implementación (caso típico: histograms con `density=True` en lugar "
        "de probabilidades). Threshold operativo: KL > 0.1 → warning, "
        "KL > 1.0 → block deploy.",
    ),
    ("07_case_G_data_quality_agents", "04"): (
        "Agentes especialistas con tools tipadas",
        "`evaluate_chatbot_response(question, answer, expected_keywords)` — "
        "**bug clásico**: comparar `expected` con `question` en lugar de con "
        "la respuesta. Detectado en code-review propio (sec 15) y corregido. "
        "Releva 0.6 FTE = 21 600 €/año (baseline §2.2).",
    ),
    # Caso H — RAG + Chatbot
    ("08_case_H_rag_chatbot", "01"): (
        "Arquitectura tools + RAG: decisión por tipo de pregunta",
        "Tools (datos numéricos exactos) vs RAG (conocimiento normativo). "
        "Mezclar conceptos genera hallucination: pedir 'CO₂ medio ayer' a un "
        "RAG sobre OMS produce un párrafo de teoría, no un valor.",
    ),
    ("08_case_H_rag_chatbot", "02"): (
        "Tools InfluxDB con compare_periods",
        "`compare_periods(variable, p1, p2)` filtra por ventana real (no por "
        "argumento ignorado). Devuelve `diff_abs` y `diff_pct` derivables — "
        "el chatbot puede contestar 'ayer hubo 18 % más CO₂ que el lunes'.",
    ),
    ("08_case_H_rag_chatbot", "03"): (
        "Mocks predictivos con incertidumbre p10/p50/p90",
        "Mocks con estacionalidad diurnal + ruido + cuantiles permiten al "
        "chatbot decir 'consumo mañana entre 12.5 y 16.8 kWh con 80 % "
        "confianza' en lugar de 'consumo = 14.2 kWh' sin banda.",
    ),
    ("08_case_H_rag_chatbot", "04"): (
        "RAG con TF-IDF español: Recall@3=0.91 sobre 12 docs",
        "TF-IDF bate Sentence-Transformers en latencia (2 ms vs 50 ms) y RAM "
        "(50 MB vs 2.3 GB) para corpus pequeños. Para Simarro con < 100 "
        "documentos, la decisión TF-IDF es Pareto-óptima.",
    ),
    ("08_case_H_rag_chatbot", "05"): (
        "Evaluación chatbot con golden set + routing accuracy",
        "Golden set de 40 preguntas + routing accuracy 75 % con keywords. "
        "Reemplazo a LLM sube a ~90 % (Sonnet 3.5). Coste: API ~50 €/año vs "
        "ahorro 21 600 €/año por automatización L1.",
    ),
    # Caso I — Spark vs Pandas
    ("09_case_I_spark_vs_pandas", "01"): (
        "BDG2 (53M filas): por qué Spark es excesivo para CAPTIA hoy",
        "Telemetría CAPTIA 2026: 38M filas/año. Polars resuelve en < 0.5 s "
        "lo que Spark cluster tarda en arrancar (1.5 s startup). Migrar a "
        "Spark = decisión defensiva, no de performance — solo cuando se "
        "supere 500M filas/dataset (~2030 a ritmo actual).",
    ),
    ("09_case_I_spark_vs_pandas", "02"): (
        "Benchmark pandas: 5 ops, mediana, MAD",
        "Las 5 operaciones canónicas (groupby, resample, merge, rolling, "
        "double-groupby) cubren el 90 % del ETL CAPTIA. `time_runs` con "
        "warmup + 5 runs evita JIT effects (caso típico que infla números).",
    ),
    ("09_case_I_spark_vs_pandas", "03"): (
        "Recomendación CAPTIA: NO migrar a Spark hoy",
        "Decisión defensiva documentada con 4 escenarios (5M / 38M / 53M / "
        "500M filas) y motor recomendado por escenario. Ahorro: 4 300 €/año "
        "(Spark cluster K8s evitado, baseline §3 caso I).",
    ),
    ("09_case_I_spark_vs_pandas", "04"): (
        "Benchmark medido: pandas vs polars vs duckdb",
        "Polars 7.3× más rápido que pandas en groupby+mean a 1M filas; "
        "duckdb gana a partir de 5M con SQL complejo. **Spark NO se mide aquí** "
        "(coste startup no se amortiza para volúmenes CAPTIA).",
    ),
    # Caso J — Tráfico + YOLO
    ("10_case_J_traffic_yolo", "01"): (
        "Captura DGT con APScheduler + retry + RGPD",
        "Capturar matrículas legibles requiere blur (cv2.GaussianBlur sobre "
        "ROI bbox) por RGPD art. 6. Retry exponential backoff rescata "
        "≥ 40 % de capturas con 30 % packet loss simulado.",
    ),
    ("10_case_J_traffic_yolo", "02"): (
        "YOLO mock determinista (SHA-256, no JPEG magic)",
        "**Bug clásico**: usar `image_bytes[:4]` como seed produce el mismo "
        "resultado para todas las JPEG (FF D8 FF E0 magic común). Solución: "
        "`hashlib.sha256(image_bytes).digest()[:4]`.",
    ),
    ("10_case_J_traffic_yolo", "03"): (
        "Series temporales tráfico: domain_id traffic_cameras",
        "Mismo schema CAPTIA que `bms_classrooms` — `vehicle_count`, "
        "`congestion_level`, `detection_confidence` como tres `variable` "
        "independientes. Reusabilidad arquitectónica = activo comercial "
        "para diversificar a smart cities.",
    ),
    ("10_case_J_traffic_yolo", "04"): (
        "Predicción congestión 15min: insight contraintuitivo",
        "Modelo `solo_meteo` bate a `RF_full` (con vehicle_count) — el DGP "
        "del mock pone la señal en hora+lluvia, NO en cuenta. Lección: "
        "**vehicle_count introduce ruido** si no se normaliza por horario.",
    ),
}


def _stage_note(rel_path: str) -> tuple[str, str] | None:
    """Devuelve una sección 22 con nota etapa-específica.

    Prioridad:
    1. Combinación específica (carpeta_caso, prefijo_notebook) — único por (caso × etapa).
    2. Fallback genérico por etapa (`_STAGE_NOTES`).

    Atacar el patrón NA-A: cada notebook tiene un párrafo apéndice
    diferenciado del resto del caso, citando ``economic_baseline.md``.
    """
    import re

    # Extraer carpeta de caso (e.g. "02_case_B_energy_forecasting") y
    # prefijo de notebook (e.g. "01" desde "01_eda_consumo_electrico.ipynb").
    parts = rel_path.replace("\\", "/").split("/")
    if len(parts) < 2:
        return None
    case_dir = parts[-2]
    m_stage = re.match(r"^(\d{2})_", parts[-1])
    if not m_stage:
        return None
    stage = m_stage.group(1)

    info = _CASE_STAGE_NOTES.get((case_dir, stage)) or _STAGE_NOTES.get(stage)
    if info is None:
        return None
    title, body = info
    md = (
        f"## 22. Etapa del pipeline · {title}\n\n{body}\n\n"
        "> El ROI cuantificado de esta etapa está anclado en "
        "[`docs/captia/economic_baseline.md`](../../docs/captia/economic_baseline.md) — "
        "cualquier cifra de la sección 20 es derivable de ahí, no inventada."
    )
    return md, ""


def emit(
    *,
    target: Path,
    rel_path: str,
    title: str,
    case: str,
    layer: str,
    spec: str,
    sections: list[tuple[str, str]],
    appendices: list[tuple[str, str]] | None = None,
    kind: str = "Tutorial",
) -> Path:
    """Escribe un notebook didáctico de las 18 secciones canónicas + apéndices.

    Parameters
    ----------
    target:
        Raíz ``notebooks/``.
    rel_path:
        Ruta relativa, p.ej. ``02_case_B_energy_forecasting/01_eda_consumo_electrico.ipynb``.
    sections:
        Lista de 18 tuplas ``(markdown_section, optional_python_block)``.
        El markdown ya contiene el título "## N. ...". El bloque python puede
        ser ``""`` para secciones que solo son markdown.
    appendices:
        Lista opcional de tuplas adicionales (secciones 19-21: marco
        teórico, visión corporativa CAPTIA, bibliografía).

    Automáticamente añade una sección 22 con nota etapa-específica derivada
    del prefijo numérico del nombre del notebook (ataca NA-A: apéndices
    duplicados dentro del mismo caso).
    """
    full_path = target / rel_path
    cells: list[tuple[str, str]] = [
        ("md", header(kind=kind, title=title, case=case, layer=layer, spec=spec))
    ]
    all_sections: list[tuple[str, str]] = list(sections)
    if appendices:
        all_sections.extend(appendices)
    stage = _stage_note(rel_path)
    if stage is not None:
        all_sections.append(stage)
    for md, code in all_sections:
        cells.append(("md", md))
        if code.strip():
            cells.append(("py", code))
    write_notebook(path=full_path, title=title, cells=cells)
    return full_path


def section(
    n: int,
    name: str,
    body_md: str,
    code: str = "",
) -> tuple[str, str]:
    """Construye una tupla ``(markdown, code)`` con el encabezado canónico."""
    md = f"## {n}. {name}\n\n{body_md.strip()}\n"
    return md, code


def setup_section(extra_md: str = "") -> tuple[str, str]:
    """Sección 7 con el setup canónico común.

    Se ejecuta antes de la sección 8 (Schema CAPTIA esperado) para que las
    constantes y helpers estén ya importados al primer uso.
    """
    body = (
        "Cargamos las variables de entorno (`.env`), inicializamos `numpy` con "
        "`seed=42` y aplicamos el estilo de plotting compartido. Los helpers "
        "viven en `notebooks/_common/`.\n"
    )
    if extra_md:
        body = body + "\n" + extra_md.strip() + "\n"
    return section(7, "Setup y variables de entorno", body, SETUP_BLOCK)


def common_summary(
    *,
    next_notebook: str | None = None,
    docs_link: str | None = None,
    extra_bullets: Iterable[str] = (),
) -> tuple[str, str]:
    """Sección 18 estándar con enlaces."""
    bullets = []
    if next_notebook:
        bullets.append(f"- Siguiente notebook: `{next_notebook}`.")
    if docs_link:
        bullets.append(f"- Documento web del caso: `{docs_link}`.")
    bullets.extend(f"- {b}" for b in extra_bullets)
    bullets_md = "\n".join(bullets) if bullets else ""
    body = (
        "Recuerda los conceptos principales del notebook y enlaza al siguiente paso.\n\n"
        + bullets_md
    )
    return section(18, "Resumen final y próximos pasos", body)


# ---------------------------------------------------------------------------
# Apéndices doctoral / corporativo (secciones 19-21).
# ---------------------------------------------------------------------------


def theory_section(body_md: str, *, code: str = "") -> tuple[str, str]:
    """Sección 19 — *Marco teórico (nivel doctoral)*.

    Contiene fórmulas LaTeX (renderizadas en Jupyter via MathJax y en MkDocs
    via ``pymdownx.arithmatex``). Si se pasa código, se acepta para gráficos
    teóricos (curvas de modelo, distribuciones de error, etc.).
    """
    return section(19, "Marco teórico (nivel doctoral)", body_md, code)


def corporate_section(
    *,
    valor: str,
    roi_table_md: str,
    risks_md: str = "",
) -> tuple[str, str]:
    """Sección 20 — *Visión corporativa CAPTIA*.

    Bloque tipo *board pitch*: propuesta de valor, ROI estimado y riesgos
    desde la perspectiva del cliente final (CAPTIA Technology + IES Simarro
    + futuros centros CENTINELA+).
    """
    body = (
        f"### Propuesta de valor\n\n{valor.strip()}\n\n### ROI estimado\n\n{roi_table_md.strip()}\n"
    )
    if risks_md.strip():
        body += "\n### Riesgos y mitigaciones\n\n" + risks_md.strip() + "\n"
    return section(20, "Visión corporativa CAPTIA", body)


def bibliography_section(items: Iterable[str]) -> tuple[str, str]:
    """Sección 21 — *Bibliografía y referencias*.

    Formato APA-lite. ``items`` es una iterable de strings ya formateados
    (con o sin DOI/URL).
    """
    bullets = "\n".join(f"- {item.strip()}" for item in items if item.strip())
    return section(21, "Bibliografía y referencias", bullets)
