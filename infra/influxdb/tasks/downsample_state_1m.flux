// Downsample on_change signals (bool_state + setpoint_step) to 1-minute rollups
//
// Source: state_events bucket (Telegraf dedup — only value changes stored)
// Stats produced:
//   last        → most recent value in window (all on_change vars)
//   count_rise  → number of 0->1 transitions (bool_state only)
//
// NOTE (Option B): duty is NOT materialized here. On_change events are sparse
// (only transitions) so mean(0/1) would be incorrect. Compute duty at query
// time with timeWeightedAvg() or stateDuration() on raw events — see
// docs/06-operations/on-change-storage.md for Grafana examples.
//
// Variable lists resolved dynamically from captia_metadata

import "array"

option task = {name: "downsample_state_1m", every: 1m, offset: 10s}

// ── Resolve variable allowlists from metadata ─────────────────────
_empty = array.from(rows: [{_value: ""}]) |> filter(fn: (r) => false)

// state_vars: bool_state signals (on_change) — produce last + count_rise
_state_meta =
  from(bucket: "captia_metadata")
    |> range(start: 0)
    |> filter(fn: (r) => r._measurement == "captia_point_meta")
    |> filter(fn: (r) => r._field == "metric_kind")
    |> group(columns: ["variable"])
    |> last()
    |> filter(fn: (r) => r._value == "bool_state")
    |> group()
    |> distinct(column: "variable")

state_vars = union(tables: [_empty, _state_meta])
  |> group()
  |> findColumn(fn: (key) => true, column: "_value")

// setpoint_vars: setpoint_step signals (on_change) — produce last only
_setpoint_meta =
  from(bucket: "captia_metadata")
    |> range(start: 0)
    |> filter(fn: (r) => r._measurement == "captia_point_meta")
    |> filter(fn: (r) => r._field == "metric_kind")
    |> group(columns: ["variable"])
    |> last()
    |> filter(fn: (r) => r._value == "setpoint_step")
    |> group()
    |> distinct(column: "variable")

setpoint_vars = union(tables: [_empty, _setpoint_meta])
  |> group()
  |> findColumn(fn: (key) => true, column: "_value")

// ── Read bool_state events from state_events bucket ─────────────
state_src =
  from(bucket: "state_events")
    |> range(start: -2m)
    |> filter(fn: (r) => r._measurement == "captia_point")
    |> filter(fn: (r) => r._field == "value")
    |> filter(fn: (r) => contains(value: r.variable, set: state_vars))
    |> toFloat()

// ── Read setpoint events from state_events bucket ───────────────
setpoint_src =
  from(bucket: "state_events")
    |> range(start: -2m)
    |> filter(fn: (r) => r._measurement == "captia_point")
    |> filter(fn: (r) => r._field == "value")
    |> filter(fn: (r) => contains(value: r.variable, set: setpoint_vars))
    |> toFloat()

// ── last: most recent value (both state + setpoint) ─────────────
state_last =
  state_src
    |> aggregateWindow(every: 1m, fn: last, createEmpty: false)
    |> set(key: "stat", value: "last")

setpoint_last =
  setpoint_src
    |> aggregateWindow(every: 1m, fn: last, createEmpty: false)
    |> set(key: "stat", value: "last")

// ── count_rise: 0→1 transitions (bool_state only) ──────────────
// In on_change mode, every event IS a value change.
// An event with _value == 1.0 means the signal transitioned FROM 0 TO 1.
// So count_rise = count of events where _value == 1.0 within the window.
// (No need for difference() — Telegraf dedup ensures only changes arrive.)
count_rise =
  state_src
    |> filter(fn: (r) => r._value == 1.0)
    |> aggregateWindow(every: 1m, fn: count, createEmpty: false)
    |> toFloat()
    |> set(key: "stat", value: "count_rise")

union(tables: [state_last, setpoint_last, count_rise])
  |> to(bucket: "telemetry_1m", org: "captia")
