"""10 Case J — Tráfico y visión artificial YOLOv (4 notebooks)."""

from __future__ import annotations

from pathlib import Path

from scripts.build_notebooks._helpers import common_summary, emit, section, setup_section
from scripts.build_notebooks._appendices import APPENDICES_CASE_J

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
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "Tags `domain_id=traffic_cameras`, `site_id=valencia`, `asset_id=DGT_CAM_*`, "
            "`variable=vehicle_count`.",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Generamos un fake JPEG.",
            """\
import io
from PIL import Image, ImageDraw

def fake_jpeg(plate_count: int = 5, *, image_seed: int = 0) -> bytes:
    \"\"\"JPEG mock con `plate_count` cajitas grises en posiciones pseudo-aleatorias.

    El parametro ``image_seed`` permite generar imagenes distintas (cada camara
    + timestamp produce un seed unico) sin perder reproducibilidad. Sin el,
    todas las imagenes son identicas.
    \"\"\"
    img = Image.new("RGB", (640, 360), (200, 200, 200))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(SEED + image_seed)
    for _ in range(plate_count):
        x = int(rng.integers(0, 600))
        y = int(rng.integers(200, 340))
        d.rectangle([x, y, x + 30, y + 12], fill=(50, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()

# 3 imágenes con plate_count distinto → bytes distintos por contenido + seed
img_bytes_a = fake_jpeg(3, image_seed=1)
img_bytes_b = fake_jpeg(7, image_seed=2)
img_bytes_c = fake_jpeg(15, image_seed=3)
print(f"JPEG mock: {len(img_bytes_a)}, {len(img_bytes_b)}, {len(img_bytes_c)} bytes (deben diferir)")
assert len({img_bytes_a, img_bytes_b, img_bytes_c}) == 3, "Imágenes mock no son distintas"
img_bytes = img_bytes_b  # mantener compatibilidad con secciones siguientes
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "**Estructura de almacenamiento + retry exponential backoff**. Path "
            "incluye hash del contenido para evitar colisiones tras reintento.",
            """\
import datetime as dt
import hashlib
import time

def store_path(camera_id: str, ts: dt.datetime, content: bytes | None = None) -> str:
    \"\"\"Path estable + nonce de contenido (8 chars md5).\"\"\"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    nonce = hashlib.md5(content).hexdigest()[:8] if content else "nocontent"
    return f"cameras/{camera_id}/{ts.strftime('%Y-%m-%d')}/{int(ts.timestamp())}_{nonce}.jpg"

def retry_with_backoff(fn, *, max_attempts: int = 3, base: float = 0.1):
    \"\"\"Retry exponential backoff: 0.1s, 0.2s, 0.4s. Levanta tras agotar intentos.\"\"\"
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(base * (2 ** attempt))
    raise last_exc if last_exc else RuntimeError("retry agotado sin excepción registrada")

print(store_path("DGT_CAM_V46_001", dt.datetime(2026, 5, 10, 12, 30, tzinfo=dt.timezone.utc), img_bytes_a))
""",
        ),
        section(
            11,
            "Transformación bronce → plata",
            "Notebook 03 transformará en counts. Aquí simulamos **scheduler + retry** "
            "sin levantar APScheduler real (que requeriría daemon).",
            """\
def capture_one(camera_id: str = "DGT_CAM_V46_001") -> dict:
    \"\"\"Captura simulada con probabilidad de fallo del 30 % para demostrar retry.\"\"\"
    rng_local = np.random.default_rng()
    if rng_local.random() < 0.3:
        raise ConnectionError(f"DGT timeout para {camera_id}")
    seed = int(time.time()) % 1000
    bytes_ = fake_jpeg(int(rng_local.integers(2, 12)), image_seed=seed)
    ts = dt.datetime.now(dt.timezone.utc)
    return {"camera_id": camera_id, "ts": ts, "size_bytes": len(bytes_),
            "path": store_path(camera_id, ts, bytes_)}

# Simular 5 disparos del scheduler (en producción: APScheduler @scheduled_job(interval, minutes=5))
captures = []
for i in range(5):
    try:
        result = retry_with_backoff(capture_one, max_attempts=3)
        captures.append({**result, "status": "ok"})
    except Exception as e:  # noqa: BLE001
        captures.append({"status": "failed", "error": str(e)[:60]})

cap_df = pd.DataFrame(captures)
print(cap_df[["status", "camera_id", "size_bytes"]].to_string(index=False))
""",
        ),
        section(
            12,
            "Construcción de capa oro",
            "Métricas operacionales del pipeline: tasa de éxito, tamaño medio, "
            "latencia. Estas son las métricas que un dashboard de operación monitoriza.",
            """\
n_ok = (cap_df["status"] == "ok").sum()
ops_metrics = {
    "captures_total": int(len(cap_df)),
    "captures_ok": int(n_ok),
    "success_rate_pct": round(100 * n_ok / max(len(cap_df), 1), 1),
    "size_avg_kb": round(cap_df.loc[cap_df["status"] == "ok", "size_bytes"].mean() / 1024, 1)
                   if n_ok > 0 else 0,
}
print(ops_metrics)
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "JPEG mock + barra de tasa éxito por intento.",
            """\
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].imshow(Image.open(io.BytesIO(img_bytes)))
axes[0].axis("off")
axes[0].set_title("JPEG mock (640x360, 7 vehiculos)")

status_count = cap_df["status"].value_counts()
status_count.plot.bar(ax=axes[1],
                     color=["#4CAF50" if s == "ok" else "#FF5722" for s in status_count.index])
axes[1].set_title(f"Captures: {ops_metrics['success_rate_pct']}% exito")
axes[1].set_ylabel("count")
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "(a) path estable + nonce; (b) `success_rate >= 50%` con retry vs ~70% sin retry; "
            "(c) RGPD compliance: documentación blur_plates como ejercicio futuro.",
            """\
ts = dt.datetime(2026, 5, 10, 12, 30, tzinfo=dt.timezone.utc)
sample_bytes = b"sample-jpeg-bytes"
path = store_path("DGT_CAM_V46_001", ts, sample_bytes)
expected = f"cameras/DGT_CAM_V46_001/2026-05-10/{int(ts.timestamp())}_{hashlib.md5(sample_bytes).hexdigest()[:8]}.jpg"
assert path == expected, f"Path inconsistente: {path}"
assert ops_metrics["success_rate_pct"] >= 40, f"Retry deberia rescatar al menos 40 % de capturas, vimos {ops_metrics['success_rate_pct']}%"
print(f"OK · path={path} · success_rate={ops_metrics['success_rate_pct']}%")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Guardar como PNG** (mucho más grande): ~5× espacio para misma info.\n"
            "2. **Sobrescribir si la cámara repite nombre**: añadir nonce de contenido.\n"
            "3. **No registrar fallos en log estructurado**: el alumno no puede "
            "investigar caídas intermitentes a posteriori.\n"
            "4. **Sin retry**: una micro-caída de red de 200 ms tira la captura.\n"
            "5. **Olvidar RGPD** (Reglamento UE 2016/679 art. 6): cámaras DGT son "
            "fuentes públicas pero capturar matrículas legibles requiere base legal "
            "(`blur_plates` con OpenCV antes de almacenar).",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Implementa `blur_plates(image)` con `cv2.GaussianBlur` sobre la "
            "ROI inferior de cada bounding box detectado por YOLO. Verifica que el "
            "OCR (Tesseract) ya no puede leer matrículas.\n"
            "2. Convierte el script en un servicio APScheduler real con "
            "`BlockingScheduler` + `@scheduled_job('interval', minutes=5)`. Logs "
            "estructurados a Loki.\n"
            "3. Añade `score_blur(image) = cv2.Laplacian(image, cv2.CV_64F).var()` y "
            "descarta capturas con `score_blur < 100` (imagen borrosa).",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Sustituir `fake_jpeg()` por `requests.get(dgt_url)` con `tenacity.retry(...)`. "
            "El resto del pipeline (`store_path`, `retry_with_backoff`, métricas ops) "
            "se mantiene sin cambios.",
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
        appendices=APPENDICES_CASE_J,
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
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "`variable ∈ {vehicle_count, congestion_level, detection_confidence}`.",
        ),
        section(
            9,
            "Carga de datos o mock",
            "Definimos un mock determinista de YOLO.",
            """\
import hashlib

CONGESTION_THRESHOLDS = (10, 30, 60)  # vehículos / 15 min — calibrado con HCM 2016

def count_vehicles_mock(image_bytes: bytes, *, threshold: float = 0.4) -> dict:
    \"\"\"Mock determinista de YOLO. Usa SHA-256 del contenido (no magic bytes JPEG).

    El cambio respecto a versiones previas: hashear toda la imagen evita que
    todas las JPEG produzcan el mismo seed (los primeros 4 bytes son el JPEG
    magic FF D8 FF E0, identico para todos los JPEG estandar).
    \"\"\"
    digest = hashlib.sha256(image_bytes).digest()
    seed = int.from_bytes(digest[:4], "big") % (2**32 - 1)
    rng = np.random.default_rng(seed)
    n = int(rng.integers(0, 60))
    conf = float(np.clip(0.7 + rng.normal(0, 0.05), 0.4, 0.99))
    cong = int(np.clip(np.digitize([n], CONGESTION_THRESHOLDS)[0], 0, 3))
    return {"vehicle_count": n, "detection_confidence": round(conf, 3),
            "congestion_level": cong}

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
    # Mosaico de píxeles aleatorios → contenido distinto por seed
    arr = rng.integers(0, 255, size=(32, 32, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO(); img.save(buf, format="JPEG", quality=85)
    results.append(count_vehicles_mock(buf.getvalue()))
results_df = pd.DataFrame(results)
print(results_df)
# Las 5 imágenes deben producir conteos distintos (no todas idénticas)
unique_counts = results_df["vehicle_count"].nunique()
assert unique_counts >= 3, f"Mock no determinista por contenido: solo {unique_counts}/5 valores únicos"
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
        appendices=APPENDICES_CASE_J,
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
        setup_section(),
        section(
            8,
            "Schema CAPTIA esperado",
            "`vehicle_count` (analog_gauge), `congestion_level` (analog_gauge), "
            "`detection_confidence` (analog_gauge).",
        ),
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
        appendices=APPENDICES_CASE_J,
    )


def _meteo(target: Path) -> Path:
    title = "Caso J · 04 Predicción congestión a 15 min — tráfico × meteorología"
    sections = [
        section(
            1,
            "Objetivo",
            "Predecir `congestion_level(t+15min)` a partir de `vehicle_count(t)`, "
            "lluvia y horario. **Predicción real con target lagged**, no "
            "clasificación contemporánea. Comparar 3 modelos:\n\n"
            "1. Baseline persistencia: `Ĉ(t+15) = C(t)`.\n"
            "2. RandomForest sobre features tiempo + meteo + cuenta.\n"
            "3. Modelo solo-meteo (sin `vehicle_count`) — para medir cuánta señal "
            "viene del tráfico vs del clima.",
        ),
        section(
            2,
            "Qué se aprende",
            "- Target lagged (`shift(-1)` en frecuencia 15-min).\n"
            "- Diagnóstico de leakage por correlación (`corr(X, y) > 0.85` ⇒ "
            "auditar el DGP del mock).\n"
            "- Multi-clase + matriz de confusión + `balanced_accuracy`.\n"
            "- Comparar modelos con/sin feature crítica para medir contribución.",
        ),
        section(
            3,
            "Contexto del caso de uso",
            "Operadores de smart city necesitan estimar congestión 15 min antes para "
            "ajustar semáforos o avisar a emergencias. La señal entra por dos canales: "
            "histórico de cuentas y meteorología. El modelo debe captar **ambos**.",
        ),
        section(
            4,
            "Relación con CENTINELA+",
            "Tool opcional `predict_congestion(camera_id, horizon_min)` para el chatbot "
            "Caso H. Cliente final: ayuntamiento o autopista, no centro educativo.",
        ),
        section(5, "Relación con Medallion", "Lee plata `traffic_cameras`, escribe oro."),
        section(
            6,
            "Datos de entrada",
            "Mock `traffic_camera_mock.csv` con DGP **mixto** (congestion_level "
            "depende de hora+lluvia+ruido categórico, no es función directa de "
            "vehicle_count).",
        ),
        setup_section(),
        section(8, "Schema CAPTIA esperado", "No aplica (oro)."),
        section(
            9,
            "Carga de datos o mock",
            "Cargamos y aplicamos **lag de 1 step (15 min)** al target. Ordenamos por "
            "(camera, timestamp) para evitar contaminación entre cámaras.",
            """\
csv_path = ROOT / "notebooks/_data/traffic_camera_mock.csv"
df = pd.read_csv(csv_path, comment="#", parse_dates=["timestamp"]).sort_values(
    ["camera_id", "timestamp"]
)
df["hour"] = df["timestamp"].dt.hour
df["weekday"] = df["timestamp"].dt.dayofweek
df["is_rush"] = ((df["hour"].isin([7, 8, 9, 17, 18, 19])) & (df["weekday"] < 5)).astype(int)
df["rain_event"] = (df["precip_mm"] > 1.0).astype(int)
df["vehicle_count_lag1"] = df.groupby("camera_id")["vehicle_count"].shift(1)
# TARGET: congestion 15 min DESPUÉS (un step de 15 min)
df["y_target"] = df.groupby("camera_id")["congestion_level"].shift(-1)
df = df.dropna(subset=["y_target", "vehicle_count_lag1"])
df["y_target"] = df["y_target"].astype(int)
print({"filas": len(df), "y_dist": df["y_target"].value_counts().to_dict()})
""",
        ),
        section(
            10,
            "Exploración paso a paso",
            "**Diagnóstico de leakage**: si `corr(vehicle_count, y_target) > 0.85` el "
            "mock está mal diseñado y el modelo será tautológico.",
            """\
corr = df[["vehicle_count", "vehicle_count_lag1", "precip_mm", "rain_event",
           "is_rush", "hour", "y_target"]].corr().round(2)
print(corr["y_target"].sort_values(ascending=False))
peak_corr = corr.loc["vehicle_count", "y_target"]
print(f"\\ncorr(vehicle_count, y_target) = {peak_corr}")
assert abs(peak_corr) < 0.85, "Probable leakage en el mock — auditar DGP"
""",
        ),
        section(11, "Transformación bronce → plata", "No aplica."),
        section(
            12,
            "Construcción de capa oro",
            "**Tres modelos** sobre split temporal estricto.",
            """\
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, classification_report, f1_score

features_full = ["vehicle_count", "vehicle_count_lag1", "precip_mm", "rain_event", "is_rush", "hour"]
features_meteo_only = ["precip_mm", "rain_event", "is_rush", "hour"]
y = df["y_target"]
X_full = df[features_full]
X_meteo = df[features_meteo_only]

# Split temporal por timestamp (mezclando cámaras OK porque ordenamos por timestamp dentro)
n = len(df); i = int(n * 0.7)
y_tr, y_te = y.iloc[:i], y.iloc[i:]
X_tr_full, X_te_full = X_full.iloc[:i], X_full.iloc[i:]
X_tr_meteo, X_te_meteo = X_meteo.iloc[:i], X_meteo.iloc[i:]

# (1) Persistencia: Ĉ(t+15) = C(t) → la observación contemporánea
y_pred_persist = df["congestion_level"].iloc[i:].to_numpy()

# (2) RF full features
rf_full = RandomForestClassifier(
    n_estimators=200, max_depth=8, class_weight="balanced",
    random_state=SEED, n_jobs=1,
).fit(X_tr_full, y_tr)
y_pred_full = rf_full.predict(X_te_full)

# (3) RF solo meteo + horario (sin tráfico)
rf_meteo = RandomForestClassifier(
    n_estimators=200, max_depth=8, class_weight="balanced",
    random_state=SEED, n_jobs=1,
).fit(X_tr_meteo, y_tr)
y_pred_meteo = rf_meteo.predict(X_te_meteo)

table = pd.DataFrame({
    "model": ["persistencia", "RF_full", "RF_solo_meteo"],
    "balanced_acc": [
        balanced_accuracy_score(y_te, y_pred_persist),
        balanced_accuracy_score(y_te, y_pred_full),
        balanced_accuracy_score(y_te, y_pred_meteo),
    ],
    "f1_macro": [
        f1_score(y_te, y_pred_persist, average="macro", zero_division=0),
        f1_score(y_te, y_pred_full, average="macro", zero_division=0),
        f1_score(y_te, y_pred_meteo, average="macro", zero_division=0),
    ],
}).round(3)
print(table)
""",
        ),
        section(
            13,
            "Visualizaciones explicativas",
            "Matriz de confusión multi-clase + feature importance + barra comparativa de modelos.",
            """\
from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(13, 4))
ConfusionMatrixDisplay.from_predictions(y_te, y_pred_full, ax=axes[0], cmap="Blues", colorbar=False)
axes[0].set_title("RF full — confusión")
imp = pd.Series(rf_full.feature_importances_, index=features_full).sort_values()
imp.plot.barh(ax=axes[1], color="#9C27B0")
axes[1].set_title("Feature importance — RF full")
table.set_index("model")[["balanced_acc", "f1_macro"]].plot.bar(ax=axes[2])
axes[2].set_title("Modelos comparados")
axes[2].tick_params(axis="x", rotation=15)
plt.tight_layout()
""",
        ),
        section(
            14,
            "Validaciones",
            "El **mejor de los modelos ML** debe batir persistencia. Si "
            "`RF_solo_meteo > RF_full`, es una señal de que `vehicle_count` "
            "introduce ruido y hay que reconsiderar el feature engineering "
            "(p.ej. usar `vehicle_count_lag` con lag mayor o normalización por "
            "horario).",
            """\
acc_persist = balanced_accuracy_score(y_te, y_pred_persist)
acc_full = balanced_accuracy_score(y_te, y_pred_full)
acc_meteo = balanced_accuracy_score(y_te, y_pred_meteo)
acc_best = max(acc_full, acc_meteo)
print(f"persistencia={acc_persist:.3f}  RF_full={acc_full:.3f}  RF_solo_meteo={acc_meteo:.3f}")
assert acc_best > acc_persist, "Ningún modelo ML bate persistencia — investigar"

if acc_meteo > acc_full + 0.02:
    print(
        "INSIGHT — solo_meteo > full por > 0.02:\\n"
        "  vehicle_count introduce ruido. El DGP de congestion_level depende "
        "principalmente de horario+lluvia. Considerar:\\n"
        "  - normalizar count por hora del día (count - count_baseline_hora);\\n"
        "  - usar lags más largos (15→60 min);\\n"
        "  - reducir profundidad del RF para evitar overfit a ruido."
    )
print("Validaciones OK")
""",
        ),
        section(
            15,
            "Errores comunes",
            "1. **Target sin lag**: predecir `C(t)` con features de `t` es "
            "clasificación, no predicción. Cualquier modelo con ground truth como "
            "input tendrá accuracy ~1.0 sin valor real.\n"
            "2. **Leakage encubierto en el mock**: `corr(X, y) > 0.85` es alarma. "
            "Auditar el DGP del simulador antes de modelar.\n"
            "3. **Comparar accuracy multi-clase desbalanceada** sin `balanced_accuracy` "
            "ni `f1_macro` — se infla con la clase mayoritaria.\n"
            "4. **No medir contribución por feature group**: si solo-meteo iguala a "
            "full, el tráfico no aporta — el caso de uso pierde sentido.\n"
            "5. **Mezclar cámaras sin estratificar**: en producción, train/test debe "
            "respetar particiones por cámara o usar ID hold-out.",
        ),
        section(
            16,
            "Ejercicios propuestos",
            "1. Cambia el horizonte a 30 min (`shift(-2)`) y mide cómo decae "
            "`balanced_accuracy`. Plotea curva accuracy vs horizonte.\n"
            "2. Implementa `OrdinalRegression` (vía `mord` o transformación binaria "
            "por nivel) y compara con RF.\n"
            "3. Auditar el mock: ¿cuál es la correlación máxima feature-target en el "
            "DGP? ¿Cómo cambiarías `synthetic_mocks.make_traffic_camera_mock` para "
            "introducir/eliminar señal?",
        ),
        section(
            17,
            "Cómo se reutiliza con datos reales",
            "Sustituir el CSV por una query Flux que cruce `traffic_cameras` (count) y "
            "`weather_station` (precipitation, wind). El feature engineering "
            "(`shift(-1)`, `rain_event`) y el RF se mantienen idénticos.",
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
        appendices=APPENDICES_CASE_J,
    )


def build(target: Path) -> int:
    _captura(target)
    _yolo(target)
    _series(target)
    _meteo(target)
    return 4
