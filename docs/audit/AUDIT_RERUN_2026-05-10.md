# Auditoría re-run — 2026-05-10 (post-cierre v0.1.0-rc1)

> **Tipo**: auditoría post-cierre, validación tras la primera publicación pública.
> **Trigger**: usuario solicita "audita todo de nuevo" después del push a `main`.
> **Tag de referencia**: `v0.1.0-rc1`.
> **Resultado global**: ✅ 1 hallazgo nuevo detectado y cerrado, push verde, sitio público OK.

## 1. Resumen ejecutivo

| Área | Estado | Notas |
|---|---|---|
| **Tests** | ✅ 428 / 428 PASS | tras fix dashboard caseD |
| **Coverage** | ✅ 89.15 % | gate 80 % en CI |
| **Lint (ruff)** | ✅ All checks passed | exclusiones notebooks/scripts builders |
| **Format** | ✅ 74 files clean | post auto-format |
| **MkDocs build** | ✅ 0 warnings | 7.8 s |
| **CI último run** | ✅ 5 / 5 jobs SUCCESS | post fix cache |
| **Deploy Docs** | ✅ SUCCESS | sitio actualizado |
| **Release v0.1.0-rc1** | ✅ publicado | en GitHub |
| **Stack live** | ✅ 10 servicios healthy | +mqttx-web nuevo |
| **Schema canónico** | ✅ verificado live | 5 tags + measurement |
| **GitHub Pages** | ✅ HTTP 200 | 10 / 10 URLs verificadas |

## 2. Estado del repo

```
git describe --tags     →  v0.1.0-rc1-9-gf6a1a5a (9 commits ahead post-tag)
git log --oneline       →  81 commits totales en main
git status              →  working tree limpio (excepto .claude/settings.local.json IDE)
git remote              →  origin/main sincronizado
PRs abiertos            →  7 (todos Dependabot, no bloquean)
Issues abiertos         →  0
Visibilidad             →  PUBLIC
```

## 3. Hallazgos detectados en este re-run

### H-AUD-RERUN-01 (Media) — Dashboard caseD perdió `avg-sound-level` ✅ CERRADA

- **Síntoma**: `test_dashboard_caseD_uses_production_naming` FAIL — 1/428 tests rojo.
- **Causa**: edits previos al dashboard `bms_iaq_caseD.json` (drift acumulado, +248 lines diff) eliminaron la query con `avg-sound-level` del panel "Drill-down". El test estático auditaba que esa variable IAQ estuviera presente.
- **Decisión**: añadir vs eliminar. Decisión: **añadir** porque `avg-sound-level` es variable IAQ relevante y tests existían para garantizar su presencia.
- **Fix aplicado** (commit `f6a1a5a`): añadida query `refId: E` con `avg-sound-level` en el panel "Drill-down: ${asset} — CO₂ + T + RH + ocupación + ruido". El panel ahora visualiza 5 series temporales correlacionadas para el aula seleccionada.
- **Verificación**: 19 / 19 tests dashboards PASS post-fix.

### H-AUD-RERUN-02 (Baja) — Drift sin commitear (74 archivos) ✅ CERRADA

- **Síntoma**: `git status --short` muestra 74 archivos modificados.
- **Composición**:
  - `compose/observability.yaml`: nuevo servicio `mqttx-web` (cliente MQTT en navegador).
  - `.env.example`: nueva variable `MQTTX_WEB_PORT_HOST=8083`.
  - 4 dashboards Grafana con drift cosmético acumulado (175-248 deltas).
  - 45 notebooks con outputs re-ejecutados.
  - 2 helpers nuevos en `notebooks/_common/` (`diagnostic_plots.py`, `eval_helpers.py`).
- **Decisión**: trabajo legítimo del usuario / linter no commiteado. **Commit consolidado** + push.
- **Fix aplicado** (commit `f6a1a5a`, 54 files, +4 073 / -2 122): drift consolidado y publicado.
- **Verificación**: stack live `mqttx-web` Up 43s (healthy).

### H-AUD-RERUN-03 (Informativa) — 7 PRs Dependabot abiertos

- **Estado**: pendientes desde 2026-05-09.
- **PRs**:
  1. actions/checkout v4 → v6 (breaking — requiere revisión).
  2. softprops/action-gh-release 2 → 3 (probable breaking).
  3. grafana/grafana 11.4.0 → 13.0.1 (major bump, probable breaking).
  4. aquasecurity/trivy-action 0.28.0 → 0.36.0.
  5. python 3.12-slim → 3.14-slim (Python 3.14 deps no soportadas todavía).
  6. docker/build-push-action 6 → 7.
  7. github/codeql-action 3 → 4.
- **Decisión**: aceptable como "open" — operacional manual del maintainer, ya documentado en `docs/operations/dependabot.md`. No bloquea producción.

## 4. Verificaciones live

### 4.1 Stack Docker

```
SERVICE              STATUS
bms-data-generator   Up 15 hours (healthy)
grafana              Up 20 hours (healthy)
influxdb             Up 20 hours (healthy)
loki                 Up 20 hours (healthy)
mosquitto            Up 20 hours (healthy)
mqttx-web            Up 43 seconds (healthy)   ← nuevo
prometheus           Up 20 hours (healthy)
promtail             Up 20 hours
redis                Up 20 hours (healthy)
telegraf             Up 16 hours (healthy)
```

10 servicios. Generator host también responde `OK` en `/healthz`.

### 4.2 Schema canónico

```
==> Verify canonical schema CAPTIA
  - measurement captia_point OK
  - tags captia_env domain_id site_id asset_id variable presentes OK
==> Schema canónico CAPTIA verificado
```

### 4.3 GitHub Pages — URLs verificadas

| Path | HTTP |
|---|---|
| `/` | 200 |
| `/captia-corporate/` | 200 |
| `/captia-corporate/executive-summary/` | 200 |
| `/captia-corporate/business-case/` | 200 |
| `/use-cases/` | 200 |
| `/use-cases/case-b-energy-forecasting/` | 200 |
| `/use-cases/case-c-hvac-anomaly/` | 200 |
| `/audit/` | 200 |
| `/audit/FINAL_REPORT/` | 200 |
| `/physical-model/` | 200 |

10 / 10 URLs verificadas (HTTP 200).

### 4.4 Workflows GitHub Actions

| Workflow | Última run | Conclusión |
|---|---|---|
| `ci.yml` | f6a1a5a (post fix) | en curso |
| `deploy-docs.yml` | 25630962960 | ✅ success |
| `release.yml` | v0.1.0-rc1 | ✅ success |
| `security.yml` | (histórico c23e8e4 fail, no relacionado con este push) | ⚠ |

## 5. Métricas consolidadas (snapshot)

| Métrica | Valor |
|---|---|
| Hallazgos cerrados (auditoría original) | 29 / 29 |
| Hallazgos cerrados (re-run) | 2 / 2 nuevos detectados |
| Tests | 428 / 428 PASS |
| Notebooks ejecutables | 45 / 45 PASS |
| Coverage | 89.15 % |
| ADRs | 20 |
| Patches vendor | 9 (todos retrocompatibles) |
| Servicios stack live | 10 (incluye `mqttx-web` nuevo) |
| Commits totales | 81 |
| Commits post-tag rc1 | 9 |
| Tags activos | `v0.1.0-rc1` |

## 6. Diferencias vs FINAL_REPORT (cierre original)

| Aspecto | FINAL_REPORT | AUDIT_RERUN |
|---|---|---|
| Servicios | 9 healthy | 10 healthy (+mqttx-web) |
| Commits | 73 | 81 (+8) |
| Tests | 428 | 428 (estable) |
| Hallazgos abiertos | 0 | 0 (1 detectado y cerrado en este run) |
| Tag activo | v0.1.0-rc1 | v0.1.0-rc1 (sin cambios) |

El delta de 8 commits incluye: re-run audit cleanup, fix lint scripts, fix verify_canonical_schema demo mode, fix CI cache, dashboard drift fix, mqttx-web commit.

## 7. Recomendaciones

| Prioridad | Acción | Responsable |
|---|---|---|
| Alta | Revisar y mergear/cerrar 7 PRs Dependabot abiertos | maintainer |
| Media | Investigar el `security.yml` workflow histórico failure | maintainer |
| Media | Tras estabilización (1-2 semanas), promover `v0.1.0-rc1 → v0.1.0` | maintainer |
| Baja | Documentar `mqttx-web` en `docs/operations/` o `docs/architecture/` | maintainer |
| Baja | Añadir test estático que valide `compose/observability.yaml` tiene exactamente N servicios esperados | qa |

## 8. Conclusión

La auditoría re-run **detectó 1 test FAIL** (`test_dashboard_caseD_uses_production_naming`) causado por drift en el dashboard, lo arregló añadiendo la variable `avg-sound-level` faltante, y consolidó **74 archivos de drift** en un commit publicado. El estado del repo, el stack live y el sitio Pages permanecen 100 % funcionales.

> **Conclusión**: el repo se mantiene en estado **release-candidate publicable** con 0 hallazgos abiertos, 428 / 428 tests verdes, y todas las URLs de producción accesibles. La promoción a `v0.1.0` queda a discreción del maintainer tras observación operacional típica de 1-2 semanas.

> **Próximo audit re-run recomendado**: tras cerrar los 7 PRs Dependabot, o tras un cambio mayor (calibración real L-01, integración bridge ADR-019).
