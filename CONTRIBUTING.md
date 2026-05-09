# Contributing to CAPTIA-SYNTHETIC-DATA-BMS

Thanks for your interest. This repository follows **Spec-Driven Development**:
the spec is the source of truth, code follows.

## Quick checklist before opening a PR

- [ ] Read the relevant spec under `docs/specs/synthetic-bms/` (01..10).
- [ ] If you change behavior, update the matching spec first or together
      with the code.
- [ ] Add or update tests so `task test` and `task test:integration` stay green.
- [ ] Run `task lint` (ruff check + format check). No warnings.
- [ ] Update `CHANGELOG.md` under `## [Unreleased]`.
- [ ] If the change is non-trivial, add an ADR entry to
      `docs/specs/synthetic-bms/09-decision-log.md`.

## Development setup

```bash
git clone https://github.com/<your-fork>/captia-synthetic-data-bms.git
cd captia-synthetic-data-bms
cp .env.example .env       # generate secrets locally; never commit .env
uv sync
task lint
task test
```

To bring up the full Docker stack locally:

```bash
task quickstart            # preflight + up + wait:healthy + smoke
```

## Repository layout (where to edit)

| Layer | Edit here? | Notes |
|-------|------------|-------|
| `vendor/synthetic-generator/` | **No** | Read-only vendored copy. Patches go to `vendor/synthetic-generator/PATCHES/`. |
| `extensions/bms_calibration/` | Yes | BMS-specific calibration & fault injection. |
| `modules/bms-data-generator/` | Yes | FastAPI control plane and services. |
| `compose/`, `infra/` | Yes | Docker compose, Mosquitto, Telegraf, InfluxDB tasks, Grafana, observability. |
| `config/` | Yes | Scenario YAMLs (`projects/`) and domain configs. |
| `docs/specs/synthetic-bms/` | Yes (with care) | Specs are normative. |
| `.claude/rules/` | With ADR | Stable rules — change requires entry in `09-decision-log.md`. |

## Coding conventions

- Python 3.12+. `uv` is the package manager.
- `ruff` is the only linter/formatter (`task lint`, `task format`).
- Type-hint everything you write. Pydantic v2 for settings and DTOs.
- Determinism: use `numpy.random.default_rng(seed)`, never `np.random.seed()`.
- Logging: structured JSON via `bms_data_generator.logging_config`. No `print`.
- Code identifiers in English (snake_case). Spec/docs in Spanish.
- Tests must use the markers in `pyproject.toml`: `unit`, `integration`,
  `smoke`, `snapshot`, `performance`, `slow`.

## Schema canónico CAPTIA (do not break)

The canonical InfluxDB / MQTT schema is **immutable**:
`captia_point` measurement, 5 tags (`captia_env`, `domain_id`, `site_id`,
`asset_id`, `variable`), single field `value` (float). Topics:
`captia/{env}/{tenant}/{site}/{device}/telemetry/{name}` and `.../event/{name}`.

If your change risks the schema, raise it in an issue first. See
`.claude/rules/002-captia-canonical-schema.md`.

## Commit style

Conventional Commits:

```
feat(bms): add IAQ index curve to bms_calibration
fix(infra): correct mosquitto healthcheck timeout
docs(specs): clarify fault probabilities in 02-domain-spec
test(api): add 401 case for /v1/control/start
chore(deps): bump pydantic to 2.13.4
```

## Pull request flow

1. Fork → branch from `main` (`feat/<short-name>`, `fix/<short-name>`, etc.).
2. Push and open a PR against `main`.
3. CI must be green (lint + tests + Docker build).
4. At least one maintainer review.
5. Squash-merge or rebase-merge — no merge commits.

## Re-vendoring `synthetic-generator`

Only maintainers re-vendor. Procedure documented in
`vendor/synthetic-generator/VENDOR.md`. Requires the env var
`CAPTIA_CONNECT_PATH` pointing to a checkout of the upstream repo.

## Reporting bugs and security issues

- Functional bugs: open a GitHub issue using the bug template.
- Security issues: do **not** open a public issue. Follow `SECURITY.md`.

## Code of Conduct

By participating, you agree to abide by `CODE_OF_CONDUCT.md`.
