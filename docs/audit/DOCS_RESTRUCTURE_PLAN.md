# Auditoría — Plan de reestructuración de `docs/` como sitio web

> Basado en el análisis del estilo y framework de `C:\CAPTIA\CAPTIA.AI\captia.ai\docs\` (subagente, 2026-05-09).

## Decisión: MkDocs + Material for MkDocs

Coincide con el resto del ecosistema CAPTIA (captia.ai docs usa exactamente esa pila), tiene auto-deploy a GitHub Pages vía Action oficial, soporta Mermaid nativo, search en español, y no requiere Node.js.

**No** Docusaurus (introduce Node), **no** VuePress, **no** Jekyll.

## Estructura objetivo

```
docs/
├── mkdocs.yml                       # ← raíz del repo, no dentro de docs/
├── assets/
│   └── stylesheets/extra.css        # paleta CAPTIA + tablas + admonitions
├── index.md                         # home con flowchart + matriz "quiero X"
├── getting-started/
│   ├── index.md                     # adaptado de QUICKSTART.md
│   └── prerequisites.md
├── guides/
│   ├── quickstart.md                # one-pager `make demo`
│   ├── live-stream.md               # cómo dejar el generator vivo
│   └── dump-export.md               # casos B/C/D
├── architecture/
│   ├── index.md                     # diagrama Mermaid de alto nivel
│   ├── data-flow.md                 # MQTT → Telegraf → InfluxDB → Grafana
│   ├── components.md                # vendor / extensions / module
│   └── decisions.md                 # ADRs index (linkea a 09-decision-log)
├── generator/
│   ├── index.md                     # qué es, dominios, hexagonal
│   ├── scenarios.md                 # 4 scenarios YAML
│   └── faults.md                    # FaultInjector + FaultEventEmitter
├── physical-model/
│   ├── index.md                     # resumen del physics-validation suite
│   ├── plausibility-rules.md
│   ├── realism-score.md
│   └── observability.md
├── scenarios/
│   ├── caso-a-pipeline-iot.md
│   ├── caso-b-consumption.md
│   ├── caso-c-faults.md
│   └── caso-d-iaq.md
├── contracts/
│   ├── mqtt-topics.md               # captia/{env}/{tenant}/...
│   ├── payload-format.md            # {"value":X,"ts_ns":N}
│   └── influx-schema.md             # measurement + 5 tags + value
├── infrastructure/
│   ├── docker-compose.md            # los 4 archivos compose
│   ├── mqtt.md                      # Mosquitto config
│   ├── telegraf.md                  # processors.regex + clone + dedup
│   ├── influxdb.md                  # 7 buckets + Flux tasks
│   ├── redis.md                     # uso (cache + Grafana Live HA)
│   └── grafana.md                   # provisioning + 4 dashboards
├── observability/
│   ├── metrics.md                   # captia_bms_* Prometheus
│   ├── logs.md                      # JSON structured + Loki
│   └── dashboards.md                # 4 dashboards documentados
├── operations/
│   ├── local-dev.md                 # make demo, make stream
│   ├── healthchecks.md              # qué monitoriza cada servicio
│   ├── troubleshooting.md           # adaptado de TROUBLESHOOTING.md
│   └── upgrade.md                   # cómo subir versiones
├── validation/
│   ├── e2e.md                       # los 10 escenarios E2E
│   ├── physical-realism.md          # link a physical-model/
│   └── anomaly-tests.md             # FaultInjector tests
├── decisions/
│   ├── index.md                     # ADRs index
│   └── adr-{001..018}.md            # auto-extraído de 09-decision-log
├── reference/
│   ├── glossary.md                  # BMS, IAQ, HVAC, ASHRAE, EN16798...
│   ├── env-vars.md                  # tabla todas las env vars
│   └── api.md                       # OpenAPI rendered
├── audit/
│   ├── STATUS.md
│   ├── 00-repo-map.md
│   ├── CONSISTENCY_MATRIX.md
│   ├── DOCS_RESTRUCTURE_PLAN.md
│   ├── AUDIT_REPORT.md              # síntesis + top 20 hallazgos
│   ├── E2E_VALIDATION_REPORT.md
│   ├── PHYSICAL_REALISM_REPORT.md
│   └── ACTION_PLAN.md
└── archive/                         # docs históricos / referencia
    ├── CENTINELA_Guia_Alumnos_v4.md
    ├── CAPTIA_Informe_CasosDeUso_DatosSinteticos.md
    ├── MEDALLION_Arquitectura_Guia_Referencia.md
    └── presentaciones/*.pptx
```

`docs/specs/` se mantiene como está (es la fuente de verdad SDD). MkDocs no la incluirá en `nav` directamente; en su lugar, cada doc del sitio enlaza a la spec correspondiente en GitHub.

## Convenciones markdown

Aplicamos las del agente captia.ai:

- **Sin** front-matter YAML — encabezado `# Título` + párrafo descriptivo + blockquote `> **Última verificación:** YYYY-MM-DD | **Fuente:** path/to/file:lineno`.
- **Énfasis con `>` blockquotes** para reglas y avisos (no `!!!`/`:::`).
- **Diagramas Mermaid** embebidos. Sin imágenes binarias salvo screenshots de Grafana en `assets/images/`.
- **Code fences** con lenguaje (`bash`, `yaml`, `json`, `python`, `flux`).
- **Tabs** vía `pymdownx.tabbed` (`=== "tab"`).
- **Tablas** Markdown puro.

## Configuración `mkdocs.yml`

```yaml
site_name: CAPTIA Synthetic Data BMS
site_description: Generador de datos sintéticos para Building Management Systems (CAPTIA)
site_url: https://jaimesendra.github.io/captia-synthetic-data-bms/
repo_url: https://github.com/jaimesendra/captia-synthetic-data-bms
repo_name: jaimesendra/captia-synthetic-data-bms
edit_uri: edit/main/docs/

theme:
  name: material
  language: es
  font:
    text: Inter
    code: JetBrains Mono
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-7
        name: Cambiar a modo oscuro
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-4
        name: Cambiar a modo claro
  features:
    - navigation.instant
    - navigation.tabs
    - navigation.tabs.sticky
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.code.annotate

extra_css:
  - assets/stylesheets/extra.css

markdown_extensions:
  - admonition
  - attr_list
  - def_list
  - footnotes
  - md_in_html
  - toc:
      permalink: true
      toc_depth: 3
  - pymdownx.details
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.keys
  - pymdownx.snippets
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.tasklist:
      custom_checkbox: true

plugins:
  - search:
      lang: es

nav:
  - Inicio: index.md
  - Empezar:
    - Introducción: getting-started/index.md
    - Pre-requisitos: getting-started/prerequisites.md
  - Guías:
    - Quickstart: guides/quickstart.md
    - Generador en vivo: guides/live-stream.md
    - Exportar dumps: guides/dump-export.md
  - Arquitectura:
    - Visión general: architecture/index.md
    - Data flow: architecture/data-flow.md
    - Componentes: architecture/components.md
    - Decisiones: architecture/decisions.md
  - Generador:
    - Vendor + extensions: generator/index.md
    - Escenarios YAML: generator/scenarios.md
    - Inyección de fallos: generator/faults.md
  - Modelo físico:
    - Resumen: physical-model/index.md
    - Reglas de plausibilidad: physical-model/plausibility-rules.md
    - Score de realismo: physical-model/realism-score.md
    - Observabilidad física: physical-model/observability.md
  - Casos de uso:
    - A — Pipeline IoT: scenarios/caso-a-pipeline-iot.md
    - B — Consumo eléctrico: scenarios/caso-b-consumption.md
    - C — Anomalías HVAC: scenarios/caso-c-faults.md
    - D — IAQ: scenarios/caso-d-iaq.md
  - Contratos:
    - Topics MQTT: contracts/mqtt-topics.md
    - Payload: contracts/payload-format.md
    - Schema InfluxDB: contracts/influx-schema.md
  - Infraestructura:
    - Compose: infrastructure/docker-compose.md
    - MQTT: infrastructure/mqtt.md
    - Telegraf: infrastructure/telegraf.md
    - InfluxDB: infrastructure/influxdb.md
    - Redis: infrastructure/redis.md
    - Grafana: infrastructure/grafana.md
  - Observabilidad:
    - Métricas: observability/metrics.md
    - Logs: observability/logs.md
    - Dashboards: observability/dashboards.md
  - Operaciones:
    - Local dev: operations/local-dev.md
    - Healthchecks: operations/healthchecks.md
    - Troubleshooting: operations/troubleshooting.md
    - Upgrade: operations/upgrade.md
  - Validación:
    - E2E: validation/e2e.md
    - Realismo físico: validation/physical-realism.md
    - Tests de anomalías: validation/anomaly-tests.md
  - Referencia:
    - Glosario: reference/glossary.md
    - Variables de entorno: reference/env-vars.md
    - API: reference/api.md
  - Auditoría:
    - STATUS: audit/STATUS.md
    - Mapa repo: audit/00-repo-map.md
    - Consistencia: audit/CONSISTENCY_MATRIX.md
    - Plan docs: audit/DOCS_RESTRUCTURE_PLAN.md
    - Reporte: audit/AUDIT_REPORT.md
    - E2E report: audit/E2E_VALIDATION_REPORT.md
    - Realismo físico: audit/PHYSICAL_REALISM_REPORT.md
    - Plan de acción: audit/ACTION_PLAN.md
```

## Workflow GitHub Pages

`.github/workflows/deploy-docs.yml`:

```yaml
name: Deploy Docs

on:
  push:
    branches: [main]
    paths:
      - "docs/**"
      - "mkdocs.yml"
      - ".github/workflows/deploy-docs.yml"
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install "mkdocs>=1.6,<2" "mkdocs-material>=9.5,<10"
      - run: mkdocs build --clean --strict
      - uses: actions/configure-pages@v4
      - uses: actions/upload-pages-artifact@v4
        with:
          path: site/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

Settings → Pages → Source = **GitHub Actions**.

URL final: `https://jaimesendra.github.io/captia-synthetic-data-bms/`.

## Migración (orden propuesto)

1. **Bootstrap** — `mkdocs.yml` + `docs/index.md` + `docs/assets/stylesheets/extra.css` + workflow.
2. **Migrar guías existentes** — `QUICKSTART.md` → `getting-started/index.md` + `guides/quickstart.md`; `TROUBLESHOOTING.md` → `operations/troubleshooting.md`.
3. **Crear contracts/** — extraer de `02-domain-spec.md` y `04-infra-spec.md` los 3 contratos (MQTT, payload, schema).
4. **Crear infrastructure/** — un doc por servicio con su config + healthcheck + ports.
5. **Crear scenarios/** — un doc por caso A/B/C/D con `curl` ejemplos + dashboard linked.
6. **Crear architecture/** — diagramas Mermaid (ya disponibles en specs).
7. **Crear physical-model/** — agregador de los 11 docs `digital-twin-bms-physics-validation`.
8. **Crear archive/** — mover `CENTINELA_*`, `CAPTIA_Informe_*`, `MEDALLION_*`, `*.pptx`.
9. **Auditoría** — los 8 docs `audit/`.
10. **Test local** — `mkdocs serve`, verificar nav, search, mermaid.
11. **Deploy** — push a main, Actions corre build + deploy.

## Archivos a marcar como obsoletos

- `docs/CENTINELA_Guia_Alumnos_v4.md` — referencia histórica → `archive/`.
- `docs/MEDALLION_Arquitectura_Guia_Referencia.md` — idem.
- `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md` — idem.
- `*.pptx` — `archive/presentaciones/`.

Ningún contenido se pierde; se reorganiza y se enlaza desde `archive/index.md`.
