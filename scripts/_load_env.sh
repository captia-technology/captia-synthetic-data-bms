#!/usr/bin/env bash
# Helper: source ./.env if present, skipping the COMPOSE_FILE line that uses
# ';' on Windows (which bash would interpret as a command separator).
# Idempotent: noop if .env doesn't exist.
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source <(grep -v '^COMPOSE_FILE=' .env | grep -E '^[A-Za-z_][A-Za-z_0-9]*=')
    set +a
fi
