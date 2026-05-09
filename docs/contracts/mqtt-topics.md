# Contrato MQTT

> **Última verificación:** 2026-05-10
> **Fuente de verdad:** `docs/specs/synthetic-bms/02-domain-spec.md` ·
> `infra/telegraf/telegraf.conf`.

## Estructura del topic

CENTINELA+ usa topics jerárquicos de **6 niveles**:

```
captia/{env}/{tenant}/{site}/{device}/{kind}/{variable}
```

| Posición | Nombre | Valores |
|---|---|---|
| 1 | constante | `captia` |
| 2 | `env` | `dev` / `staging` / `prod` |
| 3 | `tenant` | `default` salvo multi-tenancy explícita |
| 4 | `site` | `ies_simarro`, `bdg2_education`, ... |
| 5 | `device` | corresponde a `asset_id` (`AULA01`, `RTU_01`, ...) |
| 6 | `kind` | `telemetry` o `event` |
| 7 | `variable` | nombre canónico (underscore) |

## Payload JSON

```json
{
  "value": 712.0,
  "ts_ns": 1714572345000000000
}
```

- `value`: float (estados booleanos como 1.0/0.0).
- `ts_ns`: timestamp en nanosegundos epoch UTC.

## QoS y persistencia

- **QoS 1** (al menos una entrega).
- **No retain**: la telemetría es snapshot, no estado retenido.
- Telegraf escribe paralelamente a un fichero local de durabilidad (
  `telegraf_state` volume) para reimportar si InfluxDB no estaba.

## Wildcards Telegraf

```
captia/+/+/+/+/telemetry/+
captia/+/+/+/+/event/+
```

El parser regex extrae los 5 tags:

```regex
captia/([^/]+)/([^/]+)/([^/]+)/([^/]+)/[^/]+/([^/]+)
       ^env  ^tenant ^site  ^asset (telemetry|event) ^variable
```

> Telegraf no usa el tenant como tag CAPTIA — solo aparece en el topic
> para ACL granular en Mosquitto.

## ACLs Mosquitto

Convenios típicos en `mosquitto.conf`:

```
pattern read  captia/%c/+/+/+/telemetry/+
pattern write captia/%c/+/+/+/telemetry/+
```

Donde `%c` es el `clientid` autenticado.

## Diferencia telemetry vs event

- `telemetry/{variable}` — ingesta continua / on-change a `captia_point`.
- `event/{variable}` — eventos del sistema (alertas, transiciones de
  estado del job) a `captia_event` o `telemetry_events`.

## Hallazgo abierto H-01

Existe un debate documentado en `docs/audit/ACTION_PLAN.md`: el payload de
`event` ¿debe usar `ts_ns` (consistente con telemetría) o `ts` ISO 8601
(más legible en logs)? Decisión arquitectónica con upstream CAPTIA-connect.
