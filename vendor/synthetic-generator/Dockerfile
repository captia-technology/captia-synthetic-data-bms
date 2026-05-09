# Synthetic Data Generator - Docker Image
# Ref: docs/specs/migration-plan.md Section 3.1

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install with uv if available, else pip
RUN pip install --no-cache-dir .

# Copy configs and examples
COPY config/ config/
COPY examples/ examples/

# Create output directory
RUN mkdir -p outputs

# Default: BMS classrooms scenario (this vendor build is BMS-only).
ENV GENERATOR_CONFIG=/app/config/projects/bms_e2e.yaml
ENV LOG_LEVEL=INFO
ENV HEALTH_PORT=8000

# Expose health port
EXPOSE 8000

ENTRYPOINT ["python", "-m", "synthetic_generator"]
CMD ["run", "--config", "/app/config/projects/bms_e2e.yaml", "--loglevel", "INFO"]
