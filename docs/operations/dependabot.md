# Operaciones — Dependabot

> **Última verificación:** 2026-05-10
> **Cierra:** H-11 (`docs/audit/AUDIT_REPORT.md`).
> **Source:** [`.github/dependabot.yml`](https://github.com/captia-technology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/.github/dependabot.yml).

## Configuración actual

`/.github/dependabot.yml` define 4 ecosystems con cadencia semanal
(lunes 06:00 UTC):

| Ecosystem | Directorio | Etiquetas | Límite | Agrupación |
|---|---|---|---|---|
| `pip` | `/` | `dependencies`, `python` | 5 PRs | `production-dependencies` (excluye ruff, pytest*, httpx) |
| `github-actions` | `/` | `dependencies`, `github-actions` | 5 PRs | sin agrupar |
| `docker` | `/modules/bms-data-generator` | `dependencies`, `docker` | 3 PRs | sin agrupar |
| `docker` | `/infra/grafana` | `dependencies`, `docker` | 3 PRs | sin agrupar |

Total máximo de PRs simultáneos: **16**.

## Flujo de revisión recomendado

1. **Lunes-martes**: Dependabot abre PRs nuevos.
2. **Maintainer**: revisar la lista en
   [github.com/captia-technology/CAPTIA-SYNTHETIC-DATA-BMS/pulls?q=is:pr+label:dependencies](https://github.com/captia-technology/CAPTIA-SYNTHETIC-DATA-BMS/pulls?q=is%3Apr+label%3Adependencies).
3. Para cada PR, los jobs CI deciden:
   - `lint` (ruff check + format).
   - `test` (245 tests + coverage gate 80 %).
   - `compose-validate` (docker compose config).
   - `e2e-stack` (`make demo` + smoke + schema verify, H-06/H-08).
   - `docker-build` (build de la imagen del generator).
4. **Si todos pasan**: merge directo.
5. **Si fallan**: investigar, ajustar `pyproject.toml` o config Docker, push fix.

## Política de upgrades

- **Patch / minor**: merge automático tras CI verde (puede automatizarse con
  `dependabot[bot]` aprobador y `mergify` o GitHub merge queue).
- **Major**: revisión manual obligatoria. Verificar:
  - Breaking changes en CHANGELOG del paquete.
  - Tests del repo siguen verdes.
  - Cobertura del módulo afectado no baja del 80 %.
  - Si toca `synthetic-generator` upstream → verificar que los 10 patches
    del vendor (`vendor/synthetic-generator/PATCHES/`) siguen aplicables.

## Excepciones documentadas

- **`ruff`, `pytest*`, `httpx`** están excluidos del agrupado
  `production-dependencies` para que se actualicen individualmente y
  no rompan el dev loop con un PR masivo.

## Auditoría

H-11 (`AUDIT_REPORT.md`) marcaba "Dependabot abierto" como hallazgo de
auditoría. La config siempre estuvo bien definida (16 PRs/semana max,
agrupación racional, etiquetas estándar). El "abierto" se refiere a la
revisión periódica de PRs en backlog — es operacional continuo, no un
fix de código.

> Acción para el maintainer al recibir notificaciones de PRs Dependabot:
> seguir el flujo descrito arriba. La auditoría automatizada no puede
> revisar PRs externos sin credenciales — esa parte se cierra como
> "config OK + flujo documentado".

## Cómo desactivar temporalmente

Si hay un release freeze o emergencia de producción:

```bash
# Cerrar todos los PRs Dependabot pendientes (manual)
gh pr list --label dependencies --state open --json number --jq '.[].number' \
  | xargs -I{} gh pr close {} --comment "Release freeze; will re-open after $(date -d 'next monday' +%Y-%m-%d)"

# Pausar dependabot moviendo el archivo
git mv .github/dependabot.yml .github/dependabot.yml.disabled
git commit -m "chore: pause dependabot during release freeze"
```

Re-activar invirtiendo el `git mv`.
