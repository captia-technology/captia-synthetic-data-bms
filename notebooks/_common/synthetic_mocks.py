"""Generadores in-memory deterministas para no bloquear los notebooks.

Importante: estos mocks son **didácticos**, no representan datos reales.
Cada función indica qué dataset real reemplaza y qué fidelidad ofrece.
Cualquier notebook que los use debe declarar explícitamente
``# MOCK — sintético, no representa datos reales``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from notebooks._common.captia_schema import DEFAULT_SEED


@dataclass(frozen=True)
class MockMeta:
    name: str
    rows: int
    columns: list[str]
    description: str


def _rng(seed: int | None) -> np.random.Generator:
    return np.random.default_rng(DEFAULT_SEED if seed is None else seed)


def _school_calendar_mask(index: pd.DatetimeIndex) -> pd.Series:
    """Devuelve True cuando el aula está en horario lectivo (lunes–viernes 08:00–15:00)."""
    weekday_ok = index.weekday < 5  # 0=Mon..4=Fri
    hour_ok = (index.hour >= 8) & (index.hour < 15)
    not_holiday = ~(
        ((index.month == 12) & (index.day >= 22))  # Navidad inicio
        | ((index.month == 1) & (index.day <= 7))  # Navidad fin
        | ((index.month == 3) & (index.day >= 14) & (index.day <= 19))  # Fallas
        | ((index.month == 4) & (index.day >= 4) & (index.day <= 12))  # Sem Santa
        | ((index.month == 6) & (index.day >= 20))  # Verano
        | (index.month == 7)
        | (index.month == 8)
        | ((index.month == 9) & (index.day < 7))  # Verano fin
    )
    return pd.Series(weekday_ok & hour_ok & not_holiday, index=index)


def make_ingauge_aula01_mock(
    *,
    start: str = "2024-09-09",
    days: int = 7,
    freq: str = "1min",
    seed: int = DEFAULT_SEED,
) -> tuple[pd.DataFrame, MockMeta]:
    """Genera un mock In-Gauge / En-Gage tipo (CO2, T, HR, ruido, lux, ocupación).

    Reemplaza puntualmente el CSV real ``ingauge_aula01.csv`` para que un
    alumno pueda ejecutar el notebook sin descargar el dataset completo.
    """
    rng = _rng(seed)
    idx = pd.date_range(start=start, periods=days * 24 * 60, freq=freq, tz="Europe/Madrid")
    in_class = _school_calendar_mask(idx)

    # Ocupación: 0–25 personas en horario lectivo, 0 fuera
    occupancy_int = np.where(in_class, rng.integers(8, 26, size=len(idx)), 0)
    # Recreos 11:00-11:30 → vaciado parcial
    recreo = (idx.hour == 11) & (idx.minute < 30)
    occupancy_int = np.where(recreo & in_class, rng.integers(0, 6, size=len(idx)), occupancy_int)

    # CO2: 410 base + 30 ppm/persona con saturación + ruido
    base_co2 = 410 + rng.normal(0, 5, size=len(idx))
    occupancy_effect = np.minimum(35.0 * occupancy_int, 1500.0)
    co2 = base_co2 + occupancy_effect + rng.normal(0, 20, size=len(idx))
    co2 = np.clip(co2, 360, 4500)

    # Temperatura: oscilación diaria + setpoint 22 cuando hay clase
    hours = idx.hour + idx.minute / 60.0
    daily_swing = 2.0 * np.sin(2 * np.pi * (hours - 6) / 24)
    setpoint = np.where(in_class, 22.0, 19.0)
    temp_indoor = setpoint + daily_swing + rng.normal(0, 0.3, size=len(idx))

    # Humedad relativa
    rh = 45.0 + 5 * np.cos(2 * np.pi * idx.dayofyear / 365) + rng.normal(0, 4, size=len(idx))
    rh = np.clip(rh, 25, 80)

    # Sonido y luz
    noise = np.where(
        in_class, 60 + rng.normal(0, 6, size=len(idx)), 35 + rng.normal(0, 3, size=len(idx))
    )
    noise = np.clip(noise, 30, 95)
    sun_above = np.clip(np.sin(2 * np.pi * (hours - 6) / 24), 0, 1)
    lux = (sun_above * 1200) + np.where(in_class, 350, 0) + rng.normal(0, 30, size=len(idx))
    lux = np.clip(lux, 0, 2000)

    # Estado AC: encendido cuando T_indoor está por encima de 23.5 (verano) o por debajo de 20 (invierno)
    ac_state = ((temp_indoor > 23.5) | (temp_indoor < 19.5)) & in_class
    ac_state = ac_state.astype(int)

    df = pd.DataFrame(
        {
            "timestamp": idx,
            "Indoor_CO2": co2.round(1),
            "Indoor_Temp": temp_indoor.round(2),
            "Indoor_Hum": rh.round(2),
            "Indoor_Noise": noise.round(1),
            "Indoor_Lux": lux.round(1),
            "Occupied": (occupancy_int > 0).astype(int),
            "People_Count": occupancy_int.astype(int),
            "CoolingState": ac_state,
        }
    )

    meta = MockMeta(
        name="ingauge_aula01_mock",
        rows=len(df),
        columns=list(df.columns),
        description=(
            "Mock In-Gauge / En-Gage AULA01 — IES Simarro: 1 semana × 1min con horario "
            "lectivo Comunidad Valenciana. Reemplaza dataset real para uso en clase."
        ),
    )
    return df, meta


def make_bdg2_education_subset(
    *,
    n_buildings: int = 6,
    months: int = 12,
    seed: int = DEFAULT_SEED,
) -> tuple[pd.DataFrame, MockMeta]:
    """Mock subconjunto BDG2 educacional (Caso B). 6 edificios × 12 meses horarios."""
    rng = _rng(seed)
    idx = pd.date_range("2024-01-01 00:00", periods=months * 30 * 24, freq="1h", tz="UTC")
    rows = []
    for b in range(n_buildings):
        bid = f"bdg2_bldg_{b:02d}"
        # Patrón base: estacional + diario + ruido
        hours = idx.hour
        weekday = idx.weekday
        season = 1 + 0.3 * np.sin(2 * np.pi * (idx.dayofyear - 80) / 365)
        diurnal = np.where(
            (hours >= 8) & (hours < 18) & (weekday < 5),
            1 + rng.normal(0, 0.05, size=len(idx)),
            0.4 + rng.normal(0, 0.04, size=len(idx)),
        )
        base_kw = 35 + 8 * b
        power = base_kw * season * diurnal + rng.normal(0, 3, size=len(idx))
        # Vacaciones de verano: -50%
        summer = (idx.month >= 7) & (idx.month <= 8)
        power = np.where(summer, power * 0.45, power)
        # Outdoor temp síncrona
        t_out = (
            12
            + 12 * np.sin(2 * np.pi * (idx.dayofyear - 80) / 365)
            + rng.normal(0, 2, size=len(idx))
        )
        ghi = np.clip(
            900
            * np.maximum(0, np.sin(2 * np.pi * (hours - 6) / 24))
            * (0.7 + 0.3 * rng.normal(0, 1, size=len(idx))),
            0,
            1100,
        )
        rows.append(
            pd.DataFrame(
                {
                    "timestamp": idx,
                    "building_id": bid,
                    "power_kw": np.clip(power, 0, None).round(2),
                    "t_outdoor": t_out.round(2),
                    "ghi": ghi.round(0),
                }
            )
        )
    df = pd.concat(rows, ignore_index=True)
    return df, MockMeta(
        name="bdg2_education_subset_mock",
        rows=len(df),
        columns=list(df.columns),
        description=(
            "Mock 6 edificios educativos × 12 meses horarios con consumo eléctrico, "
            "T exterior y GHI. Plausible pero NO real."
        ),
    )


def make_lbnl_fdd_rtu_mock(
    *,
    days: int = 14,
    freq: str = "1min",
    seed: int = DEFAULT_SEED,
) -> tuple[pd.DataFrame, MockMeta]:
    """Mock LBNL FDD RTU con ventanas de fallo etiquetadas."""
    rng = _rng(seed)
    idx = pd.date_range("2024-06-01", periods=days * 24 * 60, freq=freq, tz="UTC")
    n = len(idx)

    t_out = (
        22 + 8 * np.sin(2 * np.pi * (idx.hour + idx.minute / 60) / 24) + rng.normal(0, 0.5, size=n)
    )
    occ = ((idx.hour >= 8) & (idx.hour < 18) & (idx.weekday < 5)).astype(int)

    # Setpoint 22 °C
    sp = np.full(n, 22.0)
    # AC enciende si T_supply < 16 (cooling) o T_supply > 26 (heating)
    t_supply_normal = sp - 6 - rng.normal(0, 0.4, size=n) * occ
    t_return_normal = sp + 1 + rng.normal(0, 0.3, size=n)
    valve = np.where(occ == 1, 1, 0)
    fan = valve.copy()

    # Inyectar fallos
    is_fault = np.zeros(n, dtype=bool)
    fault_type = np.array(["normal"] * n, dtype=object)

    # valve_stuck: 4 episodios de 2h
    for _ in range(4):
        s = int(rng.integers(60, n - 200))
        e = s + 120
        valve[s:e] = 1  # se queda abierta aunque no haga falta
        # T_supply no baja -> permanece ≈ T_return
        t_supply_normal[s:e] = t_return_normal[s:e] - 0.2
        is_fault[s:e] = True
        fault_type[s:e] = "valve_stuck"

    # sensor_drift: ventana 1 día con bias creciente
    s = int(rng.integers(60, n - 24 * 60))
    e = s + 24 * 60
    drift = np.linspace(0, 3.0, e - s)
    t_supply_normal[s:e] += drift
    is_fault[s:e] = True
    fault_type[s:e] = np.where(fault_type[s:e] == "normal", "sensor_drift", fault_type[s:e])

    # fan_failure: 3 episodios cortos
    for _ in range(3):
        s = int(rng.integers(60, n - 60))
        e = s + 30
        fan[s:e] = 0
        is_fault[s:e] = True
        fault_type[s:e] = np.where(fault_type[s:e] == "normal", "fan_failure", fault_type[s:e])

    # refrigerant_low: ventana media donde DT_supply_return colapsa
    s = int(rng.integers(60, n - 4 * 60))
    e = s + 3 * 60
    t_supply_normal[s:e] = t_return_normal[s:e] - 0.5
    is_fault[s:e] = True
    fault_type[s:e] = np.where(fault_type[s:e] == "normal", "refrigerant_low", fault_type[s:e])

    df = pd.DataFrame(
        {
            "timestamp": idx,
            "OA_TEMP": t_out.round(2),
            "SA_TEMP": t_supply_normal.round(2),
            "RA_TEMP": t_return_normal.round(2),
            "CCV": valve.astype(int),
            "FAN_STATE": fan.astype(int),
            "OCCU_MOD": occ.astype(int),
            "is_fault": is_fault.astype(int),
            "fault_type": fault_type,
        }
    )
    return df, MockMeta(
        name="lbnl_fdd_rtu_mock",
        rows=len(df),
        columns=list(df.columns),
        description="Mock LBNL FDD-style con 4 fallos etiquetados (valve_stuck, sensor_drift, fan_failure, refrigerant_low).",
    )


def make_era5_xativa_mock(
    *,
    days: int = 30,
    seed: int = DEFAULT_SEED,
) -> tuple[pd.DataFrame, MockMeta]:
    """Mock ERA5 Xàtiva (T, GHI, viento, precipitación, presión) horario."""
    rng = _rng(seed)
    idx = pd.date_range("2024-06-01", periods=days * 24, freq="1h", tz="UTC")
    n = len(idx)
    hours = idx.hour
    doy = idx.dayofyear
    # Temperatura: 18 + 10*sin(estacional) + 6*sin(diaria)
    t_celsius = (
        16
        + 10 * np.sin(2 * np.pi * (doy - 80) / 365)
        + 6 * np.sin(2 * np.pi * (hours - 6) / 24)
        + rng.normal(0, 1.0, size=n)
    )
    # GHI proporcional al sol y nubes
    sun_above = np.clip(np.sin(2 * np.pi * (hours - 6) / 24), 0, 1)
    cloud = np.clip(0.8 + 0.3 * rng.normal(0, 1, size=n), 0.2, 1.0)
    ghi = (sun_above * 950 * cloud).round(0)

    wind = np.clip(2 + 1.5 * rng.normal(0, 1, size=n), 0, None)
    precip = np.clip(rng.exponential(0.05, size=n) - 0.04, 0, 30)
    pressure = 1013 + 8 * np.sin(2 * np.pi * doy / 365) + rng.normal(0, 2, size=n)
    df = pd.DataFrame(
        {
            "timestamp": idx,
            "t_air_c": t_celsius.round(2),
            "ghi_w_m2": ghi,
            "wind_speed_ms": wind.round(2),
            "precip_mm": precip.round(2),
            "pressure_hpa": pressure.round(1),
        }
    )
    return df, MockMeta(
        name="era5_xativa_mock",
        rows=len(df),
        columns=list(df.columns),
        description="Mock ERA5 Xàtiva — 30 días horarios. NO usar para predicciones reales.",
    )


def make_traffic_camera_mock(
    *,
    cameras: tuple[str, ...] = ("DGT_CAM_V46_001", "DGT_CAM_V46_002"),
    days: int = 7,
    seed: int = DEFAULT_SEED,
) -> tuple[pd.DataFrame, MockMeta]:
    """Mock conteo vehicular sintético + meteorología fusionada.

    DGP **explícito** (evita leakage encubierto):

    - ``vehicle_count(t) = base(hour, dow) · slowdown(rain) + ruido + offset(camera)``
    - ``congestion_level(t)`` con regla MIXTA:
        1. nivel base por hora/dow,
        2. lluvia (efecto ±1 nivel cuando ``precip > 1 mm``),
        3. ruido categórico aleatorio.

    No es función directa de ``vehicle_count``; el modelo del notebook debe
    aprender la interacción ``cuenta + meteo + horario``.
    """
    rng = _rng(seed)
    rows = []
    idx = pd.date_range("2024-09-01", periods=days * 24 * 4, freq="15min", tz="UTC")
    n = len(idx)
    for cam in cameras:
        # Determinismo: hash builtin en Python varía entre procesos (PYTHONHASHSEED).
        # Usamos sha1 para asegurar misma offset en todas las ejecuciones.
        import hashlib

        offset = int.from_bytes(hashlib.sha1(cam.encode()).digest()[:4], "big") % 30
        weekday = idx.weekday
        rush = ((idx.hour.isin([7, 8, 9, 17, 18, 19])) & (weekday < 5)).astype(float)
        # Base: tráfico esperado según hora del día y día de la semana
        base = 30 + 50 * rush + 8 * np.sin(2 * np.pi * (idx.hour) / 24)
        rain = np.clip(rng.exponential(0.05, size=n) - 0.04, 0, 5)
        rain_event = (rain > 1.0).astype(float)
        slowdown = 1.0 - 0.18 * rain_event  # -18 % cuando llueve
        count = base * slowdown + rng.normal(0, 4, size=n) + offset

        # congestion_level: regla MIXTA — no es binning de count
        base_level = np.where(rush > 0, 2, np.where(idx.hour.isin([10, 11, 14, 15, 16]), 1, 0))
        rain_bump = (rain_event * rng.choice([0, 1], size=n, p=[0.4, 0.6])).astype(int)
        cat_noise = rng.choice([-1, 0, 0, 0, 1], size=n)
        congestion = np.clip(base_level + rain_bump + cat_noise, 0, 3)

        rows.append(
            pd.DataFrame(
                {
                    "timestamp": idx,
                    "camera_id": cam,
                    "vehicle_count": np.clip(count, 0, None).round(0).astype(int),
                    "congestion_level": congestion.astype(int),
                    "detection_confidence": np.clip(
                        0.85 + rng.normal(0, 0.04, size=n), 0.5, 1.0
                    ).round(3),
                    "precip_mm": rain.round(2),
                }
            )
        )
    df = pd.concat(rows, ignore_index=True)
    return df, MockMeta(
        name="traffic_camera_mock",
        rows=len(df),
        columns=list(df.columns),
        description="Mock conteo vehicular cámaras DGT + lluvia. Sintético, no real.",
    )


def make_chatbot_golden_set(seed: int = DEFAULT_SEED) -> pd.DataFrame:
    """Golden set de 40 preguntas para evaluación del chatbot Caso H."""
    questions = [
        ("data_lookup", "¿Cuál fue la temperatura media en AULA01 ayer?", "tool:query_influxdb"),
        ("data_lookup", "¿Cuántos kWh consumió AULA01 la semana pasada?", "tool:query_influxdb"),
        ("data_compare", "¿Fue más caluroso enero 2024 o enero 2023?", "tool:compare_periods"),
        ("data_compare", "¿Cuándo hubo más CO₂, lunes o miércoles?", "tool:compare_periods"),
        (
            "forecast",
            "¿Cuánto consumirá AULA01 mañana entre 9 y 12?",
            "tool:get_consumption_prediction",
        ),
        (
            "forecast",
            "¿Cuál será la temperatura exterior mañana a mediodía?",
            "tool:get_weather_prediction",
        ),
        ("anomaly", "¿Hay alguna anomalía en el HVAC ahora mismo?", "tool:check_hvac_anomaly"),
        (
            "anomaly",
            "Muéstrame los últimos 3 fallos detectados en el HVAC.",
            "tool:check_hvac_anomaly",
        ),
        ("state", "¿Está encendido el AC de AULA01?", "tool:get_building_state"),
        ("state", "¿Cuántas personas hay ahora en AULA01?", "tool:get_building_state"),
        ("rag", "¿Por qué sube el CO₂ en un aula cerrada?", "rag"),
        ("rag", "¿Qué nivel de CO₂ se considera peligroso?", "rag"),
        ("rag", "¿Qué es CENTINELA+?", "rag"),
        ("rag", "¿Qué dice la OMS sobre temperatura en aulas?", "rag"),
        ("rag", "¿Para qué sirve la arquitectura Medallion?", "rag"),
        ("rag", "¿Qué es el índice IAQ?", "rag"),
        ("data_lookup", "¿Cuál fue el pico de luminosidad ayer?", "tool:query_influxdb"),
        ("data_lookup", "¿Cuántos kW pico ha tenido AULA01 esta semana?", "tool:query_influxdb"),
        ("data_compare", "¿Hay más ruido en horario lectivo o en recreo?", "tool:compare_periods"),
        (
            "forecast",
            "¿Cuánto durará la próxima ola de calor en Xàtiva?",
            "tool:get_weather_prediction",
        ),
        ("anomaly", "¿Sospechas alguna válvula atascada?", "tool:check_hvac_anomaly"),
        ("state", "¿Qué iluminación está encendida ahora en AULA01?", "tool:get_building_state"),
        ("rag", "¿Qué normativa española aplica a la calidad del aire en aulas?", "rag"),
        ("rag", "¿Por qué CENTINELA+ usa MQTT?", "rag"),
        ("rag", "¿Para qué sirve un dump de InfluxDB?", "rag"),
        ("rag", "¿Qué es un IsolationForest?", "rag"),
        ("data_lookup", "¿Cuántas transiciones de AC ha habido este lunes?", "tool:query_influxdb"),
        ("data_lookup", "¿Cuál fue la humedad relativa media el viernes?", "tool:query_influxdb"),
        (
            "data_compare",
            "¿Consumimos más electricidad el martes o el jueves?",
            "tool:compare_periods",
        ),
        ("forecast", "¿Cuánto sol haremos mañana al mediodía?", "tool:get_weather_prediction"),
        ("anomaly", "¿Está el ventilador funcionando como debe?", "tool:check_hvac_anomaly"),
        ("state", "¿En qué velocidad está el ventilador 1 ahora?", "tool:get_building_state"),
        ("rag", "¿Qué hace Telegraf en CENTINELA+?", "rag"),
        ("rag", "¿Qué es el bucket telemetry_1h?", "rag"),
        ("rag", "¿Qué quiere decir 'bool_state'?", "rag"),
        ("rag", "¿Por qué los topics MQTT son jerárquicos?", "rag"),
        ("data_lookup", "Pico máximo de t_voc esta semana en AULA01.", "tool:query_influxdb"),
        ("data_compare", "Compara el consumo entre mayo y junio.", "tool:compare_periods"),
        (
            "forecast",
            "Predicción de consumo total para mañana en AULA01.",
            "tool:get_consumption_prediction",
        ),
        ("anomaly", "¿La temperatura de retorno se ha disparado hoy?", "tool:check_hvac_anomaly"),
    ]
    df = pd.DataFrame(questions, columns=["category", "question", "expected_mechanism"])
    rng = _rng(seed)
    df["expected_substring"] = df["category"].map(
        {
            "data_lookup": "valor",
            "data_compare": "comparación",
            "forecast": "predicción",
            "anomaly": "anomalía",
            "state": "estado",
            "rag": "explicación",
        }
    )
    df["difficulty"] = rng.choice(["easy", "medium", "hard"], size=len(df), p=[0.4, 0.4, 0.2])
    return df
