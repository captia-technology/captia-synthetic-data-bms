# bms-signal-alias

Wrapper de sink que renombra variables vendor → nombres canónicos de producción
(CAPTIA simarro-prod) antes de emit a MQTT/file/Influx.

## Por qué

El vendor `synthetic-generator` produce DataPoints con nombres internos
(`temperature`, `power`, `humidity`, ...). Producción simarro-prod usa
`temperature_01`, `power_01`, `relative-humidity`, etc.

Sin AliasSink, los datos sintéticos NO son drop-in replacement de telemetría
real: cualquier dashboard, alerta o modelo ML entrenado contra producción
falla con datos sintéticos.

Source of truth del mapping: `docs/specs/digital-twin-bms-physics-validation/11-production-signal-mapping.md`.

## Uso

```python
from bms_signal_alias import AliasSinkAdapter
from synthetic_generator.sinks.mqtt import MQTTSinkAdapter, MQTTSinkConfig

real = MQTTSinkAdapter(MQTTSinkConfig(broker_url="tcp://localhost:1883"))
aliased = AliasSinkAdapter.from_yaml(
    real_sink=real,
    yaml_path=Path("config/domains/bms_classrooms/variables.yaml"),
)
aliased.open()
aliased.emit(point)  # renames point.variable vendor → production
aliased.close()
```

## Cierre

L-PV-01 (catálogo divergente vendor↔producción), parcialmente.
T-PV-21 en `docs/specs/digital-twin-bms-physics-validation/10-implementation-readiness.md`.
