<!--
Thanks for your contribution! Please follow the checklist below.
Read CONTRIBUTING.md if this is your first PR.
-->

## Summary

<!-- 1-3 sentences describing what this PR changes and why. -->

## Type of change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing behaviour to change)
- [ ] Documentation / specs only
- [ ] Infrastructure / CI / tooling

## Spec link

<!-- Link to the spec under docs/specs/synthetic-bms/ that this change implements or updates. -->

- Spec: `docs/specs/synthetic-bms/<NN-name>.md`

## Checklist

- [ ] I read the relevant spec(s) before changing code.
- [ ] I updated the spec or added an ADR (`09-decision-log.md`) when behaviour changed.
- [ ] `task lint` passes.
- [ ] `task test` and `task test:integration` pass locally.
- [ ] I updated `CHANGELOG.md` under `## [Unreleased]`.
- [ ] I did not modify files under `vendor/synthetic-generator/`
      (or, if I did, I added a patch under `vendor/synthetic-generator/PATCHES/`).
- [ ] No secrets, real tokens, or absolute personal paths in this diff.

## Test plan

<!-- How did you test this? Commands, scenarios, screenshots if UI/dashboard related. -->

```bash
task lint
task test
task test:integration
```

## Screenshots (optional)

<!-- For Grafana / UI changes only. -->
