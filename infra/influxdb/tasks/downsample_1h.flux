// Downsample 15m rollups to 1-hour aggregates (cascade)
// Same cascade logic as 15m: preserves stat tag, correct fn per stat type.

option task = {name: "downsample_1h", every: 1h, offset: 1m}

src =
  from(bucket: "telemetry_15m")
    |> range(start: -75m)
    |> filter(fn: (r) => r._measurement == "captia_point")
    |> filter(fn: (r) => r._field == "value")

// Stats that cascade with mean
mean_stats =
  src
    |> filter(fn: (r) => r.stat == "mean" or r.stat == "duty")
    |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)

// Stats that cascade with min
min_stats =
  src
    |> filter(fn: (r) => r.stat == "min")
    |> aggregateWindow(every: 1h, fn: min, createEmpty: false)

// Stats that cascade with max
max_stats =
  src
    |> filter(fn: (r) => r.stat == "max")
    |> aggregateWindow(every: 1h, fn: max, createEmpty: false)

// Stats that cascade with sum
sum_stats =
  src
    |> filter(fn: (r) => r.stat == "count_rise" or r.stat == "sum")
    |> aggregateWindow(every: 1h, fn: sum, createEmpty: false)

// Stats that cascade with last
last_stats =
  src
    |> filter(fn: (r) => r.stat == "last")
    |> aggregateWindow(every: 1h, fn: last, createEmpty: false)

union(tables: [mean_stats, min_stats, max_stats, sum_stats, last_stats])
  |> to(bucket: "telemetry_1h", org: "captia")
