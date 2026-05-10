# =============================================================================
# CAPTIA-SYNTHETIC-DATA-BMS — Metadata Bootstrap (one-shot)
# Loads variable catalog from config/domains/<dom>/variables.yaml to bucket
# captia_metadata of InfluxDB. Adapted from captia-connect/tools/metadata-bootstrap.
# =============================================================================
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir influxdb-client==1.43.0 pyyaml==6.0.2

COPY tools/metadata-bootstrap/bootstrap.py /app/bootstrap.py
COPY tools/metadata-bootstrap/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Domain configs are mounted as volume in compose, so the YAMLs come from the
# host filesystem and changes apply without rebuilding the image.
# (Alternative: copy `config/domains` into the image for sealed-image deploys.)

ENTRYPOINT ["/app/entrypoint.sh"]
