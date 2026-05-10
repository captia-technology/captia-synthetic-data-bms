# Metadata Bootstrap

Carga el **catálogo de variables** y la **config de dominio** desde
`config/domains/<dominio>/variables.yaml` al bucket **`captia_metadata`** de
InfluxDB. Adaptado de `captia-connect/tools/metadata-bootstrap`.

## Ejecución automática (default en cada deploy)

El servicio `metadata-bootstrap` se levanta automáticamente como parte de
`compose/data-plane-init.yaml`, **después** de `influx-init` y **antes** de
que la API del generator se considere lista. Cada `make demo` o
`make quickstart` lo ejecuta con `BOOTSTRAP_MODE=force` (purga y reescribe).

```bash
make demo            # incluye metadata-bootstrap automático
make quickstart      # idem + build del generator
```

## Ejecución manual

```bash
# Re-ejecutar bootstrap con purga
docker compose -f compose/base.yaml -f compose/data-plane-init.yaml \
    run --rm metadata-bootstrap

# O directamente con Python (con InfluxDB en localhost:8087)
python tools/metadata-bootstrap/bootstrap.py \
    --url http://localhost:8087 \
    --token "$(grep INFLUXDB_TOKEN .env | cut -d= -f2)" \
    --org captia --env dev --domain bms_classrooms \
    --domains-dir config/domains --n-aulas 10 --force
```

### Modos

| Flag | Comportamiento |
|------|---------------|
| `--force` (default deploy) | Purga el catálogo del env y reescribe |
| `--skip-if-exists` | Salir 0 si ya hay metadata para `env` (idempotente) |
| `--purge-old` | Solo purga, no escribe |
| `--dry-run` | Imprime line-protocol sin escribir |
| `--diagnose` | Conectividad + 1-line write test |

Cambiar el modo del servicio Docker:

```bash
BOOTSTRAP_MODE=skip-if-exists docker compose -f ... up -d metadata-bootstrap
```

## Qué escribe

| Measurement | Tags | Campos clave | Filas (10 aulas) |
|-------------|------|--------------|-----------------|
| `captia_point_meta` | `domain_id, site_id, asset_id, variable, captia_env, asset_type` | `vendor_name, data_type, unit, category, point_type, metric_kind, storage_mode, range_min, range_max, is_actuator, display_name, ...` | 21 vars × 10 aulas = **210** |
| `captia_domain_meta` | `domain_id, site_id, captia_env` | `domain_name, namespace, modo_default, schema_version, entity_id_tag, pvn_template, pvp_template, display_name_template, bucket, measurement_strategy` | **1** |

**Adición local vs captia-connect**: si la variable tiene
`production_name:` definido en `variables.yaml`, ese se usa como tag
canónico `variable=` (alineado con simarro-prod ground truth). El nombre
vendor se preserva en el field `vendor_name` para trazabilidad.

## Correlación telemetry ↔ metadata

Tags compartidos (`domain_id`, `site_id`, `variable`, `captia_env`)
permiten JOIN entre buckets:

```flux
// Enriquecer telemetría con unit + display_name
tel = from(bucket:"telemetry")
  |> range(start: -1h)
  |> filter(fn:(r) => r._measurement == "captia_point")

meta = from(bucket:"captia_metadata")
  |> range(start: 0)
  |> filter(fn:(r) => r._measurement == "captia_point_meta")
  |> filter(fn:(r) => r._field == "display_name" or r._field == "unit")
  |> last()
  |> pivot(rowKey:["variable"], columnKey:["_field"], valueColumn:"_value")

join.tables(method: "inner", left: tel, right: meta, on: ["variable"])
```

## Códigos de salida

| Exit | Significado | Acción Docker |
|------|-------------|--------------|
| `0` | OK (escrito o skip-if-exists hit) | `service_completed_successfully` → continúa |
| `1` | Error (config, conexión, write) | Detiene dependientes |
| `130` | SIGINT | — |

## Verificación

```bash
make verify-metadata       # añadir target en Makefile

# Manualmente
TOKEN=$(grep INFLUXDB_TOKEN .env | cut -d= -f2)
curl -s -X POST "http://localhost:8087/api/v2/query?org=captia" \
  -H "Authorization: Token $TOKEN" \
  -H "Accept: application/csv" \
  -H "Content-type: application/vnd.flux" \
  -d 'from(bucket:"captia_metadata") |> range(start:0) |> filter(fn:(r) => r._measurement == "captia_point_meta") |> count() |> group() |> sum()'
```

Esperado: ~210 puntos (21 vars × 10 aulas) + 1 `captia_domain_meta`.
