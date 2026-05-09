"""Read-path service: select-bucket-by-range + Flux builder + InfluxDB call.

Implements the contract described in CENTINELA+ guide § 1.1 / § 1.3:

    "Dashboard Adapter — API REST: elige el bucket correcto según el rango
     de tiempo consultado, cachea en Redis, expone /v1/query para
     dashboards y agentes externos."

This v1 covers the bucket selector and Flux generation; the Redis cache
hook is documented and stubbed but not yet wired (out-of-scope for
gap #5 closure — see TODO at the bottom).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

LOG = logging.getLogger(__name__)


# --- Bucket selector -------------------------------------------------------

# (lower_bound_seconds, bucket_name, stat) ordered ascending.
# CENTINELA+ § 1.3 mapping:
#   - last hour → telemetry (raw, every 5s)
#   - last 24h → telemetry_1m (mean stat)
#   - last 7d  → telemetry_15m
#   - last 365d → telemetry_1h
_BUCKET_RULES: tuple[tuple[int, str, bool], ...] = (
    (3600, "telemetry", False),  # ≤ 1 h: raw
    (86400, "telemetry_1m", True),  # ≤ 24 h: 1-min rollup
    (7 * 86400, "telemetry_15m", True),  # ≤ 7 d: 15-min rollup
    (365 * 86400, "telemetry_1h", True),  # ≤ 365 d: 1-h rollup
    (10 * 365 * 86400, "telemetry_1h", True),  # cualquier > 1y: cae igualmente al 1h
)

# A relative duration like ``-15m``, ``-2h``, ``-3d``.
_REL_RE = re.compile(r"^-?(\d+)([smhd])$")


def _relative_to_seconds(spec: str) -> int | None:
    m = _REL_RE.match(spec)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    return n * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


def select_bucket(start: str) -> tuple[str, bool]:
    """Pick the correct bucket for a Flux ``range(start: ...)`` value.

    Returns ``(bucket_name, is_rollup)``. Falls back to the largest bucket
    when the range cannot be parsed.
    """
    span = _relative_to_seconds(start.lstrip("-"))
    if span is None:
        # Absolute timestamp — assume whole-year window and use 1h rollup.
        return _BUCKET_RULES[-1][1], True
    for upper, bucket, is_rollup in _BUCKET_RULES:
        if span <= upper:
            return bucket, is_rollup
    return _BUCKET_RULES[-1][1], True


# --- Flux query builder ----------------------------------------------------


@dataclass(frozen=True)
class QueryRequest:
    variable: str
    start: str = "-1h"
    stop: str = "now()"
    asset_id: str | None = None
    domain_id: str = "bms_classrooms"
    aggregation: str = "mean"  # mean|max|min|sum|last


_VALID_AGG = {"mean", "max", "min", "sum", "last", "first", "count"}


def _flux_string_literal(value: str) -> str:
    # Reject any input containing characters that could break out of the
    # Flux double-quoted string. The canonical CAPTIA tags + variables are
    # always safe ASCII identifiers (with underscore or hyphen), so we
    # allow only [a-zA-Z0-9_.-].
    if not re.fullmatch(r"[A-Za-z0-9_.\-]+", value):
        raise ValueError(f"unsafe value for Flux string literal: {value!r}")
    return f'"{value}"'


def _flux_time_expr(value: str) -> str:
    if value == "now()":
        return value
    if _relative_to_seconds(value.lstrip("-")) is not None:
        return value
    # Absolute ISO 8601 — must be safe alphanumeric + a few separators.
    if not re.fullmatch(r"[0-9TZ:.+\-]+", value):
        raise ValueError(f"unsafe time literal: {value!r}")
    return value


def build_flux(req: QueryRequest, bucket: str, is_rollup: bool) -> str:
    if req.aggregation not in _VALID_AGG:
        raise ValueError(f"unsupported aggregation: {req.aggregation}")

    parts = [
        f'from(bucket: "{bucket}")',
        f"  |> range(start: {_flux_time_expr(req.start)}, stop: {_flux_time_expr(req.stop)})",
        '  |> filter(fn: (r) => r._measurement == "captia_point")',
        f"  |> filter(fn: (r) => r.variable == {_flux_string_literal(req.variable)})",
        f"  |> filter(fn: (r) => r.domain_id == {_flux_string_literal(req.domain_id)})",
    ]
    if req.asset_id is not None:
        parts.append(f"  |> filter(fn: (r) => r.asset_id == {_flux_string_literal(req.asset_id)})")
    if is_rollup:
        parts.append(f'  |> filter(fn: (r) => r.stat == "{req.aggregation}")')
    else:
        parts.append(f"  |> aggregateWindow(every: 1m, fn: {req.aggregation}, createEmpty: false)")
    parts.append('  |> keep(columns: ["_time", "_value", "asset_id", "variable"])')
    parts.append('  |> sort(columns: ["_time"])')
    return "\n".join(parts)


# --- HTTP client ----------------------------------------------------------


@dataclass
class InfluxQueryClient:
    """Minimal async client around ``POST /api/v2/query`` (CSV result)."""

    url: str
    token: str
    org: str
    timeout_s: float = 10.0

    async def query(self, flux: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            resp = await client.post(
                f"{self.url}/api/v2/query",
                params={"org": self.org},
                content=flux.encode("utf-8"),
                headers={
                    "Authorization": f"Token {self.token}",
                    "Content-Type": "application/vnd.flux",
                    "Accept": "application/csv",
                },
            )
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"InfluxDB query failed: HTTP {resp.status_code} — {resp.text[:200]}"
                )
            return _parse_csv(resp.text)


# --- CSV parser -----------------------------------------------------------


def _parse_csv(text: str) -> list[dict]:
    """Parse the InfluxDB annotated CSV result into a list of plain dicts.

    The default annotated CSV has header rows preceded by '#'. We skip
    those, then read the first non-comment header line and emit each
    subsequent non-empty row as a dict. Empty lines and the trailing
    blank are skipped.
    """
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    if not lines:
        return []
    header = [c.strip() for c in lines[0].split(",")]
    out: list[dict] = []
    for raw in lines[1:]:
        if not raw.strip():
            continue
        cells = raw.split(",")
        # InfluxDB CSV starts every data row with an empty cell + result + table.
        row = {header[i]: cells[i] for i in range(min(len(header), len(cells)))}
        # Strip the bookkeeping columns Flux always emits.
        for k in ("", "result", "table"):
            row.pop(k, None)
        out.append(row)
    return out


# --- TODO --------------------------------------------------------------
# - Redis cache wrapper around InfluxQueryClient.query (CENTINELA+ § 1.1).
#   Key = sha256(flux) | TTL = 30 s by default. Cache hit/miss exposed as
#   Prometheus counter so dashboards can show effectiveness.
