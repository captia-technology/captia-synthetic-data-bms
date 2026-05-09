# Reporte de documentación web

> **Última verificación:** 2026-05-10

Resumen del trabajo de reestructuración de `docs/` para soportar:

1. La auditoría extrema de fases 1–10 (ya completa).
2. La nueva capa de **casos de uso, contratos, validación y notebooks** que
   convierten el repo en material docente reutilizable.

## Mapa de entregables

```
docs/
├── index.md                     # landing page (matriz "quiero X") — actualizado
├── getting-started/
│   ├── index.md                 # ya existente (camino más rápido)
│   ├── overview.md              # qué es y por qué
│   ├── local-setup.md           # uv + docker + .env
│   └── notebooks.md             # cómo ejecutar los notebooks
├── architecture/
│   ├── index.md                 # ya existente (diagrama servicios)
│   ├── medallion.md             # bronce → plata → oro
│   ├── centinela-overview.md    # arquitectura CENTINELA+ explicada
│   ├── captia-schema.md         # measurement, tags, field, line protocol
│   └── data-flow.md             # de sensor a Grafana paso a paso
├── use-cases/
│   ├── index.md                 # tabla resumen
│   ├── case-a-pipeline-iot.md
│   ├── case-b-energy-forecasting.md
│   ├── case-c-hvac-anomaly.md
│   ├── case-d-iaq-occupancy.md
│   ├── case-e-weather-solar.md
│   ├── case-f-mlops.md
│   ├── case-g-data-quality-agents.md
│   ├── case-h-rag-chatbot.md
│   ├── case-i-spark-pandas.md
│   └── case-j-traffic-yolo.md
├── notebooks/
│   ├── index.md                 # cómo navegar las 42 entradas
│   ├── how-to-run.md            # entornos, kernel, .env
│   └── notebook-map.md          # tabla con enlaces a cada notebook
├── contracts/
│   ├── influx-schema.md         # measurement + 5 tags + field + buckets + retención
│   ├── mqtt-topics.md           # estructura topic + payload + QoS
│   ├── variable-catalog.md      # 24 variables canónicas + alias
│   └── medallion-layers.md      # qué se permite en cada capa
├── validation/
│   ├── e2e.md                   # tests integración + smoke
│   ├── data-quality.md          # reglas calidad bronce/plata/oro
│   ├── physical-realism.md      # link al PHYSICAL_REALISM_REPORT
│   └── ml-validation.md         # criterios para Casos B/C/D
├── operations/
│   ├── troubleshooting.md       # ya existente como TROUBLESHOOTING.md (link)
│   ├── environment.md           # variables y secretos
│   └── docker.md                # compose layouts y orden de arranque
├── audit/
│   ├── STATUS.md                # ya existente; añadidos hitos notebooks
│   ├── USE_CASE_MATRIX.md       # nuevo
│   ├── NOTEBOOK_PLAN.md         # nuevo
│   ├── DOCS_REPORT.md           # este documento
│   └── (resto sin cambios)
├── archive/
│   └── (sin cambios)
└── specs/
    └── (sin cambios)
```

## Decisiones de información

- **Una página por caso** (`use-cases/case-*.md`) con: objetivo, datos,
  capas Medallion, notebooks asociados (links), errores comunes, criterios
  de validación.
- **Contratos separados** en `docs/contracts/` para que los integradores
  externos solo necesiten esa carpeta.
- **Validación separada** en `docs/validation/` para que QA y review
  encuentren rápido las reglas activas.
- **Notebooks tienen su propio mapa** en `docs/notebooks/` para que los
  alumnos no tengan que abrir GitHub.
- **No se duplica contenido**: cada nuevo doc enlaza al spec correspondiente
  en `docs/specs/synthetic-bms/` o `docs/specs/digital-twin-bms-physics-validation/`
  cuando ese es la fuente de verdad.

## Estilo

- Markdown CommonMark + extensiones MkDocs (`pymdownx.*`).
- Diagramas Mermaid en bloques ` ```mermaid `.
- Tablas con anchos razonables (no exceder 4–5 columnas).
- Cada documento empieza con `> **Última verificación:** 2026-05-10` y
  enlaza a su fuente de verdad.

## Validación

```bash
# Validación local
uv run --with mkdocs-material mkdocs build --strict   # estricto donde se pueda
uv run --with mkdocs-material mkdocs serve --dev-addr 0.0.0.0:8000

# Workflow ya configurado
.github/workflows/deploy-docs.yml  # build + deploy a GitHub Pages
```

> Nota: `strict: false` se mantiene en `mkdocs.yml` porque hay enlaces
> relativos a rutas de código (`vendor/...`, `modules/...`) que mkdocs
> trataría como ficheros rotos. La política de la auditoría es no romper
> esos enlaces.

## Pendientes documentales

- [ ] Generar el sitio en GitHub Pages tras el merge.
- [ ] Vincular `notebooks/` a la web mediante `mkdocs-jupyter` (decisión
  diferida v1.1; por ahora se enlaza al `.ipynb` directamente).
- [ ] Internacionalización EN para fragmentos clave (decisión diferida).
