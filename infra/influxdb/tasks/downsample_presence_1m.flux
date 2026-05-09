// Downsample bool_presence signals to 1-minute rollups: duty + count_rise + last
// duty = mean of 0/1 values (ratio of time active)
// count_rise = number of 0->1 transitions (e.g. pieces detected)
// Variable list resolved dynamically from captia_metadata (metric_kind = "bool_presence")

import "array"

option task = {name: "downsample_presence_1m", every: 1m, offset: 10s}

// ── Resolve variable allowlist from metadata ──────────────────────
_empty = array.from(rows: [{_value: ""}]) |> filter(fn: (r) => false)

_meta =
  from(bucket: "captia_metadata")
    |> range(start: 0)
    |> filter(fn: (r) => r._measurement == "captia_point_meta")
    |> filter(fn: (r) => r._field == "metric_kind")
    |> group(columns: ["variable"])
    |> last()
    |> filter(fn: (r) => r._value == "bool_presence")
    |> group()
    |> distinct(column: "variable")

presence_vars = union(tables: [_empty, _meta])
  |> group()
  |> findColumn(fn: (key) => true, column: "_value")

src =
  from(bucket: "telemetry")
    |> range(start: -2m)
    |> filter(fn: (r) => r._measurement == "captia_point")
    |> filter(fn: (r) => r._field == "value")
    |> filter(fn: (r) => contains(value: r.variable, set: presence_vars))
    |> toFloat()

duty =
  src
    |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
    |> set(key: "stat", value: "duty")

count_rise =
  src
    |> group(columns: ["captia_env", "domain_id", "site_id", "asset_id", "variable", "_measurement", "_field"])
    |> sort(columns: ["_time"])
    |> difference(nonNegative: false)
    |> filter(fn: (r) => r._value == 1)
    |> aggregateWindow(every: 1m, fn: count, createEmpty: false)
    |> toFloat()
    |> set(key: "stat", value: "count_rise")

last_val =
  src
    |> aggregateWindow(every: 1m, fn: last, createEmpty: false)
    |> set(key: "stat", value: "last")

union(tables: [duty, count_rise, last_val])
  |> to(bucket: "telemetry_1m", org: "captia")
