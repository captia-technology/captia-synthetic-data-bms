#!/usr/bin/env bash
# =============================================================================
# update_vendor.sh — re-vendoriza synthetic-generator desde CAPTIA-CONNECT.
# =============================================================================
set -euo pipefail

UPSTREAM="${CAPTIA_CONNECT_PATH:-}"
SRC="${UPSTREAM}/tools/synthetic-generator"
DST="vendor/synthetic-generator"

if [ -z "${UPSTREAM}" ]; then
    echo "ERROR: set CAPTIA_CONNECT_PATH to a checkout of the upstream repo"
    echo "       export CAPTIA_CONNECT_PATH=/path/to/captia-connect"
    exit 1
fi
if [ ! -d "${SRC}" ]; then
    echo "ERROR: source not found: ${SRC}"
    exit 1
fi

echo "==> Re-vendoring synthetic-generator desde ${SRC}"

# Save VENDOR.md and PATCHES dir to merge after copy
cp "${DST}/VENDOR.md" "/tmp/VENDOR.md.bak" 2>/dev/null || true

if command -v robocopy >/dev/null 2>&1; then
    robocopy "${SRC}" "${DST}" /MIR /XD .venv .pytest_cache .ruff_cache __pycache__ /XF *.pyc *.pyo /NFL /NDL /NJH /NJS /NC /NS /NP || true
else
    rsync -a --delete --exclude .venv --exclude .pytest_cache --exclude .ruff_cache --exclude __pycache__ --exclude '*.pyc' "${SRC}/" "${DST}/"
fi

# Restore VENDOR.md (manual update of date/commit)
mv "/tmp/VENDOR.md.bak" "${DST}/VENDOR.md" 2>/dev/null || true

UPSTREAM_COMMIT=$(git -C "${UPSTREAM}" rev-parse HEAD 2>/dev/null || echo "unknown")
echo "  - upstream commit: ${UPSTREAM_COMMIT}"
echo "==> Vendor sync completo. Actualiza VENDOR.md manualmente con commit y fecha."
