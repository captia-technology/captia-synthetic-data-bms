# Validación end-to-end

> **Última verificación:** 2026-05-10
> **Reportes detallados:** `docs/audit/E2E_VALIDATION_REPORT.md`.

## Suites de tests

Tres marcas (`pytest -m`):

- `unit` — sin I/O, rápidas (ms).
- `integration` — requieren MQTT / InfluxDB / Redis; usan stack vivo.
- `smoke` — post-deploy health verification.

```bash
task test                      # unit
task test:integration          # integración
task smoke                     # smoke post-deploy
```

## 10 escenarios E2E ejecutados (mayo 2026)

Documentados en `docs/audit/E2E_VALIDATION_REPORT.md`. Resumen:

1. **Live mode 60 min, seed=42** — 700+ puntos/aula·h, hash de muestra
   reproducible.
2. **Backfill 12 meses, dump line-protocol** — `output/{site}_12m.lp.gz`
   válido.
3. **Caso C con `BMS_FAULTS_ENABLED=true`** — 4 tipos de fallos en
   `captia_fault_labels`.
4. **Caso D 1-min config** — bucket `telemetry_1m` con CO₂ + T + ocupación.
5. **Healthcheck 8 servicios** — `docker compose ps` muestra `healthy`.
6. **Schema canónico via Flux** — los 5 tags y `value` en cada serie.
7. **Telegraf reset** — durabilidad volume preserva mensajes.
8. **Grafana dashboards** — 4 datasources + 4 dashboards provisionados.
9. **Prometheus scraping** — métricas de Telegraf (1.32) y bms-data-generator.
10. **Loki + Promtail** — logs JSON estructurados.

## Suite total

**211/211 PASS** (snapshot mayo 2026). Ver
[`audit/STATUS.md`](../audit/STATUS.md).

## Validación notebooks

```bash
uv run python -c "
import json, pathlib
nbs = sorted(pathlib.Path('notebooks').rglob('*.ipynb'))
ok = sum(1 for nb in nbs if json.loads(nb.read_text(encoding='utf-8')).get('nbformat') == 4)
print(f'{ok}/{len(nbs)} notebooks ok')
"
```

Esperado: `45/45 notebooks ok`.

## Continous Integration

Ver `.github/workflows/`:

- `ci.yml` — `task lint` + `task test`.
- `deploy-docs.yml` — `mkdocs build` + deploy GitHub Pages.

Coverage gating: 80 % (baseline 89.15 %).
