# Vendoring snapshot — synthetic-generator

- **Source repository**: `C:\CAPTIA\CAPTIA-CONNECT\captia-connect`
- **Source path**: `tools/synthetic-generator/`
- **Snapshot date**: 2026-05-09
- **Upstream version (pyproject.toml)**: 0.1.0
- **Upstream commit (CAPTIA-CONNECT HEAD)**: `2a793a551967dde4d35c94d2b636f07130dcd72f`
- **Patches applied**: ninguno (snapshot inicial)

## Política

- **Read-only**: este directorio NO se edita directamente.
- **Re-vendoring**: vía `scripts/update_vendor.sh` (Fase 9), que:
  - Copia archivos del upstream con robocopy + exclusiones (caches).
  - Aplica parches en `vendor/synthetic-generator/PATCHES/NNN-titulo.patch`.
  - Actualiza este `VENDOR.md` con commit y fecha nuevos.
- **Parches**: registrar en `vendor/synthetic-generator/PATCHES/` con formato `NNN-descripcion.patch` y referencia ADR en `docs/specs/synthetic-bms/09-decision-log.md`.

## Contenido

```
vendor/synthetic-generator/
├── pyproject.toml      # paquete `synthetic-generator` v0.1.0
├── Dockerfile
├── README.md
├── src/synthetic_generator/
│   ├── core/           # núcleo zero-deps
│   ├── ports/          # protocols hexagonales
│   ├── domains/        # bms_classrooms, industrial_refrigeration, discrete_manufacturing
│   └── sinks/          # mqtt, file, stdout, null, composite
├── tests/              # unit, integration, snapshot
├── examples/
└── config/
```

## Uso

Importar como package del workspace:

```python
from synthetic_generator.core.runner import ScenarioRunner
from synthetic_generator.domains.registry import get_domain
from synthetic_generator.sinks.mqtt import MQTTSinkAdapter
```

## Verificación

```bash
uv sync
uv run python -c "from synthetic_generator.core.runner import ScenarioRunner; print(ScenarioRunner.__module__)"
```
Debe imprimir `synthetic_generator.core.runner`.
