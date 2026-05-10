# Presentaciones internas — REVISIÓN PENDIENTE antes de exposición pública

> ⚠️ **Estos PPTX están commiteados en el repo y, al hacerlo público, serán
> visibles en GitHub.** Pueden contener información sensible (URLs internas
> de tenants, capturas con tokens, IDs de clientes). Revisar antes del
> primer release público.

## Archivos en esta carpeta

| Archivo | Tamaño | Contenido (resumen) | Estado |
|---------|--------|---------------------|--------|
| `captia-connect-partner-integration.pptx` | 742 KB | Contrato canónico CAPTIA-CONNECT v1.0 (mayo 2026). Topics MQTT, schema InfluxDB, integración partners. | 🔍 Revisar |
| `influxdb-simarro-buckets.pptx` | 769 KB | Snapshot ground truth `simarro-prod` (marzo 2026). Variables reales en AULA01, ~30 señales. | 🔍 Revisar |

## Cómo revisar

1. Abrir cada PPTX y comprobar slide a slide:
   - URLs internas (ej. `*.simarro-prod.captiatechnology.com`).
   - Tokens, claves o credenciales en capturas.
   - Datos personales o de cliente identificables.
   - Logos/assets de partners con licencia restringida.

2. Si **todo es apto para repo público** → eliminar este aviso y dejar los archivos.

3. Si hay contenido sensible:
   - **Opción A — Sanitizar**: redactar las slides afectadas y re-commitear.
   - **Opción B — Mover a repo privado**: eliminar de este repo, conservar en
     `captia-connect` o `captia-internal-docs`. Comando:
     ```bash
     git rm docs/archive/presentaciones/*.pptx
     echo 'docs/archive/presentaciones/*.pptx' >> .gitignore
     git commit -m "chore(security): remove internal pptx from public repo"
     ```
   - **Opción C — Reescribir historia**: si ya estaba expuesto y contenía
     secretos críticos, usar `git filter-repo` para purgar del historial
     (operación destructiva, requiere coordinación).

## Referencias en el código que dependen de estos PPTX

Si decides moverlos, actualiza también las referencias en:

```
config/domains/bms_classrooms/variables.yaml:9
docs/specs/digital-twin-bms-physics-validation/00-open-questions.md:15
docs/specs/digital-twin-bms-physics-validation/11-production-signal-mapping.md:5,15
```

## Decisión por defecto (status actual)

Los archivos quedan **en el repo** mientras el repositorio aún es **privado**.
Antes de hacer público el repo (release v0.1.0):

- [ ] Maintainer revisa cada slide manualmente.
- [ ] Decisión registrada en `CHANGELOG.md` (sección [Unreleased]).
- [ ] Aviso eliminado o actualizado.

> **Maintainer**: Jaime Sendra · jaime.sendra@captiatechnology.com
