# Regla 003 — Política de vendoring

## Qué se vendoriza

`vendor/synthetic-generator/` es copia controlada de `C:\CAPTIA\CAPTIA-CONNECT\captia-connect\tools\synthetic-generator` en una versión específica.

## Reglas

1. **Read-only**: no editar archivos en `vendor/synthetic-generator/`.
2. Toda extensión va en `extensions/bms_calibration/` o `modules/bms-data-generator/`.
3. Cambios upstream se incorporan vía script `scripts/update_vendor.sh` que:
   - Copia archivos del upstream.
   - Aplica parches registrados en `vendor/synthetic-generator/PATCHES/`.
   - Actualiza `vendor/synthetic-generator/VENDOR.md` con commit upstream y fecha.
4. Si se necesita parchear, registrar en `09-decision-log.md` y aplicar como diff en `vendor/synthetic-generator/PATCHES/NNN-titulo.patch`.

## Anti-patrón

- Editar `vendor/` directamente.
- Mezclar lógica BMS-específica en `vendor/`.
- Re-vendorizar sin actualizar `VENDOR.md`.
