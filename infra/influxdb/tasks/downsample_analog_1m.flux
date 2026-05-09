// Downsample analog_gauge signals to 1-minute rollups: mean + min + max
// Variable list resolved dynamically from captia_metadata (metric_kind = "analog_gauge")

import "array"

option task = {name: "downsample_analog_1m", every: 1m, offset: 10s}

// ── Resolve variable allowlist from metadata ──────────────────────
// Safe: returns [] if metadata is not yet loaded (task is a no-op, no error)
_empty = array.from(rows: [{_value: ""}]) |> filter(fn: (r) => false)

_meta =
  from(bucket: "captia_metadata")
    |> range(start: 0)
    |> filter(fn: (r) => r._measurement == "captia_point_meta")
    |> filter(fn: (r) => r._field == "metric_kind")
    |> group(columns: ["variable"])
    |> last()
    |> filter(fn: (r) => r._value == "analog_gauge")
    |> group()
    |> distinct(column: "variable")

analog_vars = union(tables: [_empty, _meta])
  |> group()
  |> findColumn(fn: (key) => true, column: "_value")

src =
  from(bucket: "telemetry")
    |> range(start: -2m)
    |> filter(fn: (r) => r._measurement == "captia_point")
    |> filter(fn: (r) => r._field == "value")
    |> filter(fn: (r) => contains(value: r.variable, set: analog_vars))

mean_agg =
  src
    |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
    |> set(key: "stat", value: "mean")

min_agg =
  src
    |> aggregateWindow(every: 1m, fn: min, createEmpty: false)
    |> set(key: "stat", value: "min")

max_agg =
  src
    |> aggregateWindow(every: 1m, fn: max, createEmpty: false)
    |> set(key: "stat", value: "max")

union(tables: [mean_agg, min_agg, max_agg])
  |> to(bucket: "telemetry_1m", org: "captia")
