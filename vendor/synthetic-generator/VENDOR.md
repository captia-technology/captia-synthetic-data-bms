# Vendoring snapshot — synthetic-generator (BMS-only)

This directory is a **read-only vendored copy** of the upstream
`synthetic-generator` engine, slimmed to ship only the `bms_classrooms`
domain. Edits live in `extensions/bms_calibration/` and
`modules/bms-data-generator/`, never here.

## Snapshot metadata

| Field | Value |
|-------|-------|
| Snapshot date | 2026-05-09 |
| Upstream version (pyproject.toml) | 0.1.0 |
| Upstream commit | `2a793a551967dde4d35c94d2b636f07130dcd72f` |
| Patches applied | `PATCHES/001-bms-only.patch` |

> The upstream repository is internal to CAPTIA Technology and not part of
> this public release. Maintainers re-vendor with
> `scripts/update_vendor.sh` against an internal checkout (path passed via
> the `CAPTIA_CONNECT_PATH` env var).

## Patches

Patches under `PATCHES/` document every modification applied on top of the
upstream snapshot. They must be re-applied after each re-vendoring.

- `001-bms-only.patch` — Removed the `industrial_refrigeration` and
  `discrete_manufacturing` domains, their configs, examples and tests.
  Updated `domains/__init__.py`, `domains/registry.py`, `Dockerfile`
  default config, `README.md` and the vendor unit/integration tests that
  referenced those domains.

## Policy

- Read-only at the parent repo level. No direct edits.
- Re-vendoring procedure:
  1. Set `CAPTIA_CONNECT_PATH` to a checkout of the upstream repo.
  2. Run `bash scripts/update_vendor.sh`.
  3. Re-apply every patch in `PATCHES/` (in lexical order).
  4. Update the *Snapshot metadata* table above with the new commit/date.
  5. Run `uv run pytest -m unit -q` and `uv run pytest -m snapshot -q`.
- New patches require an ADR entry in
  `docs/specs/synthetic-bms/09-decision-log.md`.

## Layout

```
vendor/synthetic-generator/
├── pyproject.toml          # synthetic-generator 0.1.0
├── Dockerfile              # default scenario: BMS classrooms
├── README.md
├── VENDOR.md               # this file
├── PATCHES/                # diffs applied on top of the snapshot
│   └── 001-bms-only.patch
├── src/synthetic_generator/
│   ├── core/               # zero-dep core (config, runner, validator…)
│   ├── ports/              # hexagonal Protocols
│   ├── domains/            # only bms_classrooms ships in this build
│   └── sinks/              # mqtt / file / stdout / null / composite
├── config/
│   ├── domains/bms_classrooms/
│   └── projects/bms_e2e.yaml
└── examples/bms-baseline.yaml
```

## Verification

```bash
uv sync
uv run python -c "from synthetic_generator.core.runner import ScenarioRunner; print(ScenarioRunner.__module__)"
```

Expected: `synthetic_generator.core.runner`.
