// Downsample 1m rollups to 15-minute aggregates (cascade)
// Preserves the stat tag and applies correct aggregation per stat type:
//   mean → mean, min → min, max → max, duty → mean,
//   count_rise → sum, last → last, sum → sum

option task = {name: "downsample_15m", every: 15m, offset: 30s}

src =
  from(bucket: "telemetry_1m")
    |> range(start: -20m)
    |> filter(fn: (r) => r._measurement == "captia_point")
    |> filter(fn: (r) => r._field == "value")

// Stats that cascade with mean
mean_stats =
  src
    |> filter(fn: (r) => r.stat == "mean" or r.stat == "duty")
    |> aggregateWindow(every: 15m, fn: mean, createEmpty: false)

// Stats that cascade with min
min_stats =
  src
    |> filter(fn: (r) => r.stat == "min")
    |> aggregateWindow(every: 15m, fn: min, createEmpty: false)

// Stats that cascade with max
max_stats =
  src
    |> filter(fn: (r) => r.stat == "max")
    |> aggregateWindow(every: 15m, fn: max, createEmpty: false)

// Stats that cascade with sum
sum_stats =
  src
    |> filter(fn: (r) => r.stat == "count_rise" or r.stat == "sum")
    |> aggregateWindow(every: 15m, fn: sum, createEmpty: false)

// Stats that cascade with last
last_stats =
  src
    |> filter(fn: (r) => r.stat == "last")
    |> aggregateWindow(every: 15m, fn: last, createEmpty: false)

union(tables: [mean_stats, min_stats, max_stats, sum_stats, last_stats])
  |> to(bucket: "telemetry_15m", org: "captia")
