"""Rate limiting central (H-03, AUDIT_REPORT.md).

Cierra el hallazgo de endpoints ``/v1/*`` sin rate limiting. Usa slowapi
sobre IP del cliente (header ``X-Forwarded-For`` si existe, sino
``request.client.host``).

Endpoints expuestos a rate limit:
    - POST /v1/control/start     (10/minute) — lanza un job pesado
    - POST /v1/datasets/export   (5/minute)  — backfill, costoso
    - POST /v1/query             (60/minute) — read-path, más permisivo

/healthz, /readyz, /metrics no se limitan (probes legítimos de
infrastructure como Prometheus o Kubernetes).
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Default: storage en memoria (proceso único). Para multi-réplica usar
# storage_uri="redis://...".
limiter = Limiter(key_func=get_remote_address, default_limits=[])


__all__ = ["RateLimitExceeded", "limiter"]
