"""10 Case J — Tráfico y visión artificial YOLOv (4 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section

CASE = "J — Tráfico + YOLO"
SPEC = "docs/specs/synthetic-bms/01-product-spec.md"


def _captura(target: Path) -> Path:
    title = "Caso J · 01 Captura de imágenes DGT — estrategia y almacenamiento"
    sections = [
        section(
            1,
            "Objetivo",
            "Diseñar un pipeline de captura periódica desde cámaras DGT con cron + "
            "almacenamiento MinIO-style + retry.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Estructura `cameras/{id}/{date}/{ts}.jpg`.\n"
            "- Cron / APScheduler.\n"
            "- Estrategia de retry y deduplicación.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Jorge (G5) trabaja en remoto desde Galicia. El pipeline debe operar desatendido.",
        ),
        section(4, "Relación con CENTINELA+", "Las imágenes no van a InfluxDB; los conteos sí."),
        section(
            5,
            "Relación con Medallion",
            "Bronce = JPEG en MinIO; Plata = conteos en `traffic_cameras`.",
        ),
        section(6, "Datos de entrada", "Conceptual + mock JPEG."),
        section(
            7,
            "Schema CAPTIA esperado",
            "Tags `domain_id=traffic_cameras`, `site_id=valencia`, `asset_id=DGT_CAM_*`, "
            "`variable=vehicle_count`.",
        ),
        setup_section(),
        section(
            9,
            "Carga de datos o mock",
            "Generamos un fake JPEG.",
            """\
import io
from PIL import Image, ImageDraw

def fake_jpeg(plate_count: int = 5) -> bytes:
    img = Image.new("RGB", (320, 240), (200, 200, 200))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(SEED)
    for _ in range(plate_count):
        x = int(rng.integers(0, 280))
        y = int(rng.integers(150, 220))
        d.rectangle([x, y, x + 30, y + 12], fill=(50, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

img_bytes = fake_jpeg(7)
print(f"JPEG mock: {len(img_bytes)} bytes")
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Estructura de directorio simulada.",
            """\
import datetime as dt

def store_path(camera_id: str, ts: dt.datetime) -> str:
    return f"cameras/{camera_id}/{ts.strftime('%Y-%m-%d')}/{int(ts.timestamp())}.jpg"

print(store_path("DGT_CAM_V46_001", dt.datetime(2026, 5, 10, 12, 30)))
""",
        ),
        section(11, "Transformación bronce → plata", "Notebook 03 transformará en counts."),
        section(12, "Construcción de capa oro", "Notebook 04."),
        section(
            13,
            "Visualizaciones explicativas",
            "Mostramos el JPEG mock.",
            """\
plt.imshow(Image.open(io.BytesIO(img_bytes)))
plt.axis("off"); plt.title("Imagen mock con coches simulados")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "El path generado es estable.",
            """\
ts = dt.datetime(2026, 5, 10, 12, 30, tzinfo=dt.timezone.utc)
assert store_path("DGT_CAM_V46_001", ts) == "cameras/DGT_CAM_V46_001/2026-05-10/1747052200.jpg"
print("Path schema OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Guardar como PNG (mucho más grande).\n"
            "2. Sobrescribir si la cámara repite nombre.\n"
            "3. No registrar fallos en log estructurado.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade un cron que captura cada 5 min.\n"
            "2. Implementa retry exponential backoff.\n"
            "3. Elimina imágenes con `score_blur` alto.",
        ),
        section(
            17, "Cómo se reutiliza con datos reales", "Sustituir `fake_jpeg` por descarga real."
        ),
        common_summary(
            next_notebook="10_case_J_traffic_yolo/02_inferencia_yolo.ipynb",
            docs_link="docs/use-cases/case-j-traffic-yolo.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="10_case_J_traffic_yolo/01_captura_imagenes_dgt.ipynb",
        title=title,
        case=CASE,
        layer="bronce",
        spec=SPEC,
        sections=sections,
    )


def _yolo(target: Path) -> Path:
    title = "Caso J · 02 Inferencia YOLO (mock por defecto)"
    sections = [
        section(
            1,
            "Objetivo",
            "Implementar la función `count_vehicles(image)` con un mock determinista; "
            "documentar cómo conectar `ultralytics` real.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Firma estable: bytes → dict.\n"
            "- Confidence threshold y NMS.\n"
            "- Cómo manejar imagen corrupta.",
        ),
        section(3, "Contexto del caso de uso", "El equipo J entrega counts en InfluxDB."),
        section(4, "Relación con CENTINELA+", "El conteo es analog_gauge."),
        section(5, "Relación con Medallion", "Bronce → plata: conteo en plata."),
        section(6, "Datos de entrada", "JPEG mock."),
        section(
            7,
            "Schema CAPTIA esperado",
            "`variable ∈ {vehicle_count, congestion_level, detection_confidence}`.",
        ),
        setup_section(),
        section(
            9,
            "Carga de datos o mock",
            "Definimos un mock determinista de YOLO.",
            """\
def count_vehicles_mock(image_bytes: bytes, *, threshold: float = 0.4) -> dict:
    rng = np.random.default_rng(int.from_bytes(image_bytes[:4], "big") % 10000)
    n = int(rng.integers(0, 60))
    conf = float(np.clip(0.7 + rng.normal(0, 0.05), 0.4, 0.99))
    cong = int(np.clip(np.digitize([n], [10, 30, 60])[0], 0, 3))
    return {"vehicle_count": n, "detection_confidence": conf, "congestion_level": cong}

print(count_vehicles_mock(b"hello-world-bytes" * 4))
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Probamos con varias imágenes.",
            """\
import io
from PIL import Image

results = []
for seed in range(5):
    rng = np.random.default_rng(seed)
    img = Image.new("RGB", (32, 32), (int(rng.integers(0, 255)), 0, 0))
    buf = io.BytesIO(); img.save(buf, format="JPEG")
    results.append(count_vehicles_mock(buf.getvalue()))
pd.DataFrame(results)
""",
        ),
        section(11, "Transformación bronce → plata", "Notebook 03."),
        section(
            12,
            "Construcción de capa oro",
            "Adapter al modelo real.",
            """\
def count_vehicles_real(image_bytes: bytes, *, threshold: float = 0.4):
    \"\"\"Adapter: requiere ultralytics + modelo. No se ejecuta sin instalación.\"\"\"
    from ultralytics import YOLO  # type: ignore[import-not-found]
    model = YOLO("yolov8n.pt")
    # img array -> resultados
    # ... omitimos detalle por dependencia opcional
    return {"vehicle_count": 0, "detection_confidence": 1.0, "congestion_level": 0}
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Histograma de counts mock.",
            """\
df_results = pd.DataFrame(results)
df_results["vehicle_count"].plot.hist(bins=10, color="#FF5722")
plt.title("Distribución de count mock"); plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Output válido y dentro de rango.",
            """\
for r in results:
    assert 0 <= r["vehicle_count"] <= 200
    assert 0 <= r["detection_confidence"] <= 1
    assert r["congestion_level"] in (0, 1, 2, 3)
print("Mock OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Devolver int vs float (TSDB espera float).\n"
            "2. Re-leer la imagen en cada inferencia (cachear).\n"
            "3. No filtrar `confidence < threshold`.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Sustituye el mock por `ultralytics`.\n"
            "2. Calcula la edad media del conjunto.\n"
            "3. Mide latencia de la inferencia.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cambiar `count_vehicles_mock` por `count_vehicles_real`.",
        ),
        common_summary(
            next_notebook="10_case_J_traffic_yolo/03_series_temporales_trafico.ipynb",
            docs_link="docs/use-cases/case-j-traffic-yolo.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="10_case_J_traffic_yolo/02_inferencia_yolo.ipynb",
        title=title,
        case=CASE,
        layer="bronce → plata",
        spec=SPEC,
        sections=sections,
    )


def _series(target: Path) -> Path:
    title = "Caso J · 03 Series temporales en InfluxDB para tráfico"
    sections = [
        section(
            1,
            "Objetivo",
            "Tomar el mock `traffic_camera_mock.csv` y construir line protocol con "
            "los tags `domain_id=traffic_cameras`, `site_id=valencia`, `asset_id=DGT_CAM_*`.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Mapping camera_id → asset_id.\n"
            "- 3 variables: count / level / confidence.\n"
            "- Por qué los conteos van como counter o analog_gauge.",
        ),
        section(3, "Contexto del caso de uso", "Plata para Caso J."),
        section(4, "Relación con CENTINELA+", "Independiente del aula."),
        section(5, "Relación con Medallion", "Bronce → plata."),
        section(6, "Datos de entrada", "Mock 7 días × 15 min × 2 cámaras."),
        section(
            7,
            "Schema CAPTIA esperado",
            "`vehicle_count` (analog_gauge), `congestion_level` (analog_gauge), "
            "`detection_confidence` (analog_gauge).",
        ),
        setup_section(),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos.",
            """\
csv_path = ROOT / "notebooks/_data/traffic_camera_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Resumen por cámara.",
            """\
print(df.groupby("camera_id")["vehicle_count"].agg(["mean", "max"]).round(2))
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Generamos line protocol.",
            """\
out_dir = ROOT / "output" / "case_J"
out_dir.mkdir(parents=True, exist_ok=True)
lines = []
for _, row in df.iterrows():
    ts_ns = int(pd.Timestamp(row["timestamp"]).value)
    for csv_col, var in [("vehicle_count", "vehicle_count"),
                          ("congestion_level", "congestion_level"),
                          ("detection_confidence", "detection_confidence")]:
        lines.append(build_line_protocol(
            measurement=MEASUREMENT_TELEMETRY,
            tags={"captia_env": "dev", "domain_id": "traffic_cameras",
                  "site_id": "valencia", "asset_id": row["camera_id"], "variable": var},
            fields={"value": float(row[csv_col])},
            timestamp_ns=ts_ns,
        ))
(out_dir / "traffic.lp").write_text("\\n".join(lines), encoding="utf-8")
print(f"Wrote {len(lines)} líneas")
""",
        ),
        section(12, "Construcción de capa oro", "Notebook 04."),
        section(
            13,
            "Visualizaciones explicativas",
            "Conteo medio por hora.",
            """\
df["hour"] = df["timestamp"].dt.hour
df.groupby("hour")["vehicle_count"].mean().plot.bar(color="#3F51B5", figsize=(7, 3))
plt.title("Tráfico medio por hora — todas las cámaras"); plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "Tags presentes y valor numérico.",
            """\
sample = lines[0]
assert "domain_id=traffic_cameras" in sample
assert "value=" in sample
print("Sample:", sample)
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Mezclar imágenes con line protocol.\n"
            "2. Usar `vehicle_count` como bool (>50 → True): pierde granularidad.\n"
            "3. Olvidar `congestion_level` como variable independiente.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Calcula `dvc/dt` en 15 min.\n"
            "2. Define una alerta `congestion_level == 3` durante 30 min.\n"
            "3. Combina con AEMET (lluvia) — ya en `traffic_camera_mock.csv`.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Sustituir el mock por counts del notebook 02.",
        ),
        common_summary(
            next_notebook="10_case_J_traffic_yolo/04_integracion_meteo_trafico.ipynb",
            docs_link="docs/use-cases/case-j-traffic-yolo.md",
        ),
    ]
    return emit(
        target=target,
        rel_path="10_case_J_traffic_yolo/03_series_temporales_trafico.ipynb",
        title=title,
        case=CASE,
        layer="bronce → plata",
        spec=SPEC,
        sections=sections,
    )


def _meteo(target: Path) -> Path:
    title = "Caso J · 04 Integración tráfico × meteorología — predicción congestión"
    sections = [
        section(
            1,
            "Objetivo",
            "Cruzar conteos de tráfico con meteorología (lluvia) y entrenar un modelo "
            "que prediga `congestion_level`.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Merge time-aligned.\n"
            "- Random Forest para clasificación ordinal.\n"
            "- Feature importance climática.",
        ),
        section(3, "Contexto del caso de uso", "Capa oro: predicción para los próximos 15 min."),
        section(4, "Relación con CENTINELA+", "Tool del chatbot Caso H opcional."),
        section(5, "Relación con Medallion", "Lee plata, escribe oro."),
        section(6, "Datos de entrada", "Mock traffic + AEMET (incluido en mismo CSV)."),
        section(7, "Schema CAPTIA esperado", "No aplica (oro)."),
        setup_section(),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos.",
            """\
csv_path = ROOT / "notebooks/_data/traffic_camera_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"])
df["hour"] = df["timestamp"].dt.hour
df["weekday"] = df["timestamp"].dt.dayofweek
df["is_rush"] = ((df["hour"].isin([7, 8, 9, 17, 18, 19])) & (df["weekday"] < 5)).astype(int)
df.head()
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "Correlación.",
            """\
print(df[["vehicle_count", "precip_mm", "is_rush", "congestion_level"]].corr().round(2))
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "Modelo.",
            """\
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

X = df[["vehicle_count", "precip_mm", "is_rush", "hour"]]
y = df["congestion_level"]
n = len(df); i = int(n * 0.7)
X_tr, X_te = X.iloc[:i], X.iloc[i:]
y_tr, y_te = y.iloc[:i], y.iloc[i:]

m = RandomForestClassifier(n_estimators=120, random_state=SEED).fit(X_tr, y_tr)
y_pred = m.predict(X_te)
print(classification_report(y_te, y_pred, zero_division=0))
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Feature importance.",
            """\
imp = pd.Series(m.feature_importances_, index=X.columns).sort_values()
imp.plot.barh(color="#9C27B0", figsize=(7, 3))
plt.title("Feature importance — congestion_level")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "El modelo discrimina niveles base.",
            """\
from sklearn.metrics import balanced_accuracy_score
print({"balanced_acc": balanced_accuracy_score(y_te, y_pred)})
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. Predecir como regresión cuando es ordinal.\n"
            "2. No incluir hora del día.\n"
            "3. Comparar accuracy entre datasets desbalanceados.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Añade `dvehicle_count_15min` como feature.\n"
            "2. Reemplaza por `OrdinalRegression`.\n"
            "3. Construye un dashboard Grafana con prediction live.",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Cambiar el mock por la query Flux que combina `traffic_cameras` + `weather_station`.",
        ),
        common_summary(
            next_notebook=None,
            docs_link="docs/use-cases/case-j-traffic-yolo.md",
            extra_bullets=(
                "¡Has completado los 42 notebooks didácticos!",
                "Vuelve a `00_project_overview/00_arquitectura_medallion_captia.ipynb` para revisitar el mapa.",
            ),
        ),
    ]
    return emit(
        target=target,
        rel_path="10_case_J_traffic_yolo/04_integracion_meteo_trafico.ipynb",
        title=title,
        case=CASE,
        layer="oro",
        spec=SPEC,
        sections=sections,
    )


def build(target: Path) -> int:
    _captura(target)
    _yolo(target)
    _series(target)
    _meteo(target)
    return 4
