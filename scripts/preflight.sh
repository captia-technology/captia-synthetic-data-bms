#!/usr/bin/env bash
# =============================================================================
# preflight.sh — comprueba que todo está en orden antes de levantar el stack.
#
# Diseñado para ser amigable: cada error tiene un mensaje claro y una pista
# de cómo arreglarlo.
# =============================================================================
set -euo pipefail

err()  { printf '\033[31mERROR\033[0m %s\n' "$*" >&2; }
warn() { printf '\033[33mAVISO\033[0m %s\n' "$*"; }
ok()   { printf '\033[32m  OK \033[0m %s\n' "$*"; }
info() { printf '       %s\n' "$*"; }

echo "==> Preflight CAPTIA-SYNTHETIC-DATA-BMS"

# 1. Docker daemon
if ! command -v docker >/dev/null 2>&1; then
    err "docker no está en PATH"
    info "Instala Docker Desktop desde https://www.docker.com/products/docker-desktop"
    exit 1
fi
if ! docker info >/dev/null 2>&1; then
    err "el daemon de Docker no responde"
    info "Asegúrate de que Docker Desktop está iniciado y espera 30 s antes de reintentar."
    exit 1
fi
ok "docker $(docker version --format '{{.Server.Version}}' 2>/dev/null || echo '?') corriendo"

# 2. Docker Compose v2
if ! docker compose version >/dev/null 2>&1; then
    err "docker compose v2 no disponible"
    info "Actualiza Docker Desktop (la versión moderna ya incluye compose v2)."
    exit 1
fi
ok "docker compose $(docker compose version --short 2>/dev/null || echo '?') disponible"

# 3. .env (auto-generar si falta)
if [ ! -f .env ]; then
    info ".env no existe — generando con secretos aleatorios…"
    bash scripts/init_env.sh
fi
ok ".env presente"

# 4. Variables que NO pueden quedar como CHANGE_ME
missing=()
for var in INFLUXDB_TOKEN INFLUXDB_ADMIN_PASSWORD BMS_API_TOKEN; do
    val=$(grep -E "^${var}=" .env 2>/dev/null | cut -d= -f2- || true)
    if [ -z "${val:-}" ] || [ "${val}" = "CHANGE_ME_USE_OPENSSL_RAND" ]; then
        missing+=("${var}")
    fi
done
if [ ${#missing[@]} -gt 0 ]; then
    warn "variables sin valor real en .env: ${missing[*]}"
    info "Ejecuta 'make init-env-force' para regenerarlas."
fi

# 5. Puertos host libres
declare -A ports=(
    [MQTT_PORT_HOST]=1884
    [MQTT_WS_PORT_HOST]=9102
    [INFLUXDB_PORT_HOST]=8087
    [GRAFANA_PORT_HOST]=3001
    [BMS_GENERATOR_PORT_HOST]=8120
    [PROMETHEUS_PORT_HOST]=9090
    [LOKI_PORT_HOST]=3100
)
busy=()
for var in "${!ports[@]}"; do
    val=$(grep -E "^${var}=" .env 2>/dev/null | cut -d= -f2- || true)
    port="${val:-${ports[$var]}}"
    # Use docker to check (cross-platform — works on Windows + Linux + macOS).
    if docker run --rm --network host alpine:3 sh -c "nc -z 127.0.0.1 ${port} 2>/dev/null" >/dev/null 2>&1; then
        # 0 = something is listening on that port already; flag only if not one of our containers
        owner=$(docker ps --format '{{.Names}} {{.Ports}}' | grep -E ":${port}->" | awk '{print $1}' | head -n1 || true)
        if [ -z "${owner}" ] || ! echo "${owner}" | grep -q "^captia-bms-"; then
            busy+=("${var}=${port} (otro proceso)")
        fi
    fi
done
if [ ${#busy[@]} -gt 0 ]; then
    warn "puertos ocupados (cambialos en .env): ${busy[*]}"
fi

# 6. Disco
free_kb=$(df -k . | awk 'NR==2 {print $4}')
free_gb=$(( free_kb / 1024 / 1024 ))
if [ "${free_gb}" -lt 5 ]; then
    warn "menos de 5 GB libres en disco (${free_gb} GB) — algunos volúmenes pueden quedar al límite"
else
    ok "${free_gb} GB libres en disco"
fi

# 7. Conflicto con otra red captia-network compartida
network_name=$(grep -E "^CAPTIA_NETWORK_NAME=" .env 2>/dev/null | cut -d= -f2- || true)
network_name="${network_name:-captia-bms-network}"
if [ "${network_name}" = "captia-network" ]; then
    foreign=$(docker network inspect captia-network 2>/dev/null \
        | python -c "import json,sys; d=json.load(sys.stdin)[0]; print(' '.join(c['Name'] for c in d.get('Containers', {}).values() if not c['Name'].startswith('captia-bms-')))" 2>/dev/null \
        || echo "")
    if [ -n "${foreign}" ]; then
        warn "la red 'captia-network' está compartida con otros contenedores: ${foreign}"
        info "Cambia CAPTIA_NETWORK_NAME=captia-bms-network en .env para aislar este stack."
    fi
fi
ok "red Docker objetivo: ${network_name}"

echo "==> Preflight OK"
