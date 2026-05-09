# syntax=docker/dockerfile:1.6
FROM python:3.12-slim AS builder
WORKDIR /build
RUN pip install --no-cache-dir uv==0.5.18

# Copia el workspace completo para resolución de dependencias entre miembros.
COPY pyproject.toml uv.lock ./
COPY vendor/synthetic-generator/ ./vendor/synthetic-generator/
COPY extensions/bms_calibration/ ./extensions/bms_calibration/
COPY modules/bms-data-generator/ ./modules/bms-data-generator/

RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install \
        -e vendor/synthetic-generator \
        -e extensions/bms_calibration \
        -e modules/bms-data-generator

FROM python:3.12-slim AS runtime
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --shell /bin/bash --uid 10001 bmsapp

COPY --from=builder /opt/venv /opt/venv
COPY vendor/synthetic-generator/ ./vendor/synthetic-generator/
COPY extensions/bms_calibration/ ./extensions/bms_calibration/
COPY modules/bms-data-generator/src/ ./modules/bms-data-generator/src/
COPY config/ ./config/

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BMS_DEFAULT_CONFIG=/app/config/projects/bms_v1_demo.yaml \
    BMS_OUTPUT_DIR=/app/output

RUN mkdir -p /app/output && chown -R bmsapp:bmsapp /app/output

USER bmsapp
EXPOSE 8120
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8120/healthz || exit 1

CMD ["python", "-m", "bms_data_generator"]
