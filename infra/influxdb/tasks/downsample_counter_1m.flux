// Downsample counter signals to 1-minute rollups: sum via difference(nonNegative)
// All counters are cumulative_monotonic: value grows monotonically.
// difference() extracts delta per sample, then sum() aggregates deltas per window.
// Variable list resolved dynamically from captia_metadata (metric_kind = "counter")

import "array"

option task = {name: "downsample_counter_1m", every: 1m, offset: 10s}

// ── Resolve variable allowlist from metadata ──────────────────────
_empty = array.from(rows: [{_value: ""}]) |> filter(fn: (r) => false)

_meta =
  from(bucket: "captia_metadata")
    |> range(start: 0)
    |> filter(fn: (r) => r._measurement == "captia_point_meta")
    |> filter(fn: (r) => r._field == "metric_kind")
    |> group(columns: ["variable"])
    |> last()
    |> filter(fn: (r) => r._value == "counter")
    |> group()
    |> distinct(column: "variable")

counter_vars = union(tables: [_empty, _meta])
  |> group()
  |> findColumn(fn: (key) => true, column: "_value")

src =
  from(bucket: "telemetry")
    |> range(start: -2m)
    |> filter(fn: (r) => r._measurement == "captia_point")
    |> filter(fn: (r) => r._field == "value")
    |> filter(fn: (r) => contains(value: r.variable, set: counter_vars))
    |> toFloat()

delta_sum =
  src
    |> group(columns: ["captia_env", "domain_id", "site_id", "asset_id", "variable", "point_type", "_measurement", "_field"])
    |> sort(columns: ["_time"])
    |> difference(nonNegative: true)
    |> aggregateWindow(every: 1m, fn: sum, createEmpty: false)
    |> set(key: "stat", value: "sum")

delta_sum
  |> to(bucket: "telemetry_1m", org: "captia")
