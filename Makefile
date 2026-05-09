# =============================================================================
# CAPTIA-SYNTHETIC-DATA-BMS — Makefile (autónomo, sin dependencia de Taskfile)
# Wraps docker compose + uv + ruff + pytest commands so that `make <target>`
# is enough on a fresh checkout.
# =============================================================================

SHELL          := bash
.SHELLFLAGS    := -eu -o pipefail -c
.DEFAULT_GOAL  := help

ENV_FILE       ?= .env

# Si .env existe, leerlo y exportar todas las KEY=VALUE para que las recetas
# bash dispongan de $$INFLUXDB_TOKEN, $$BMS_API_TOKEN, $$GRAFANA_PORT_HOST...
# Saltamos cualquier línea que contenga ';' (formato Windows COMPOSE_FILE) o
# que no sea una asignación válida.
ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
EXPORTED_ENV_VARS := $(shell awk -F= '/^[A-Za-z_][A-Za-z_0-9]*=/ && $$0 !~ /;/ {print $$1}' $(ENV_FILE))
export $(EXPORTED_ENV_VARS)
endif

COMPOSE_FILES  := -f compose/base.yaml -f compose/observability.yaml -f compose/generator.yaml -f compose/data-plane-init.yaml
COMPOSE_INFRA  := -f compose/base.yaml -f compose/observability.yaml -f compose/data-plane-init.yaml
COMPOSE        := docker compose --env-file $(ENV_FILE) $(COMPOSE_FILES)
COMPOSE_NOGEN  := docker compose --env-file $(ENV_FILE) $(COMPOSE_INFRA)

# Fallback if .env doesn't exist yet (avoids docker compose failing eagerly).
ENV_GUARD = @if [ ! -f $(ENV_FILE) ]; then bash scripts/init_env.sh; fi

.PHONY: help
help:  ## Print available targets
	@awk 'BEGIN {FS = ":.*##"; printf "Available targets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# -----------------------------------------------------------------------------
# Bootstrap / lifecycle
# -----------------------------------------------------------------------------

.PHONY: init-env
init-env:  ## Generate .env with random secrets (idempotent)
	bash scripts/init_env.sh

.PHONY: init-env-force
init-env-force:  ## Recreate .env with new random secrets
	bash scripts/init_env.sh --force

.PHONY: install
install:  ## uv sync the workspace (Python 3.12 + workspace members)
	uv sync

.PHONY: preflight
preflight:  ## Validate Docker, ports and .env
	bash scripts/preflight.sh

.PHONY: quickstart
quickstart: init-env install preflight up wait-healthy wait-init smoke urls  ## One-shot completo (incluye build de bms-data-generator)
	@echo ""
	@echo "==> Listo. Abre Grafana en http://localhost:$${GRAFANA_PORT_HOST:-3001} (admin/admin)."

.PHONY: quickstart-infra
quickstart-infra: init-env install preflight up-infra wait-healthy-infra wait-init smoke-infra urls  ## quickstart pero solo la infra (sin build del generator)

.PHONY: demo
demo: init-env preflight up-infra wait-healthy-infra wait-init smoke-infra urls  ## ⭐ MODO ALUMNO: arranca toda la infra y la valida (sin build del generator)
	@echo ""
	@echo "================================================================"
	@echo "  Stack BMS listo. Lo siguiente que puedes hacer:"
	@echo "================================================================"
	@echo " 1. Abre Grafana:    http://localhost:$${GRAFANA_PORT_HOST:-3001}"
	@echo "                     usuario: admin   contrasenya: admin"
	@echo " 2. (Opcional) lanza el generador en tu host (otra terminal):"
	@echo "       make run-host"
	@echo " 3. Cuando termines:"
	@echo "       make down       # apaga el stack (mantiene datos)"
	@echo "       make clean      # apaga y borra todos los volumenes"
	@echo "================================================================"

.PHONY: up
up:  ## docker compose up -d (full stack, builds bms-data-generator)
	$(ENV_GUARD)
	$(COMPOSE) up -d

.PHONY: up-infra
up-infra:  ## docker compose up -d (infra only — no bms-data-generator)
	$(ENV_GUARD)
	$(COMPOSE_NOGEN) up -d

.PHONY: down
down:  ## docker compose down (preserves volumes)
	$(COMPOSE) down

.PHONY: clean
clean:  ## docker compose down -v (DELETES volumes)
	$(ENV_GUARD)
	$(COMPOSE) down -v

.PHONY: ps
ps:  ## docker compose ps
	$(COMPOSE) ps

.PHONY: logs
logs:  ## docker compose logs -f --tail=100 (use SERVICE=<name> to filter)
	$(COMPOSE) logs -f --tail=100 $(SERVICE)

.PHONY: config-render
config-render:  ## Print the merged compose configuration
	$(COMPOSE) config

# -----------------------------------------------------------------------------
# Healthchecks / smoke
# -----------------------------------------------------------------------------

.PHONY: wait-healthy
wait-healthy:  ## Block until all 9 services report healthy (max 120s)
	bash scripts/wait_healthy.sh

.PHONY: wait-init
wait-init:  ## Block until influx-init exits successfully (max 60s)
	@deadline=$$(( $$(date +%s) + 60 )); \
	while [ $$(date +%s) -lt $$deadline ]; do \
	    state=$$(docker inspect --format='{{.State.Status}}' captia-bms-influx-init 2>/dev/null || echo missing); \
	    code=$$(docker inspect --format='{{.State.ExitCode}}' captia-bms-influx-init 2>/dev/null || echo 0); \
	    if [ "$$state" = "exited" ] && [ "$$code" = "0" ]; then echo "==> influx-init OK"; exit 0; fi; \
	    if [ "$$state" = "exited" ] && [ "$$code" != "0" ]; then echo "ERROR: influx-init exited with code $$code"; docker logs captia-bms-influx-init | tail -20; exit 1; fi; \
	    sleep 2; \
	done; \
	echo "ERROR: timeout waiting for influx-init"; \
	docker logs captia-bms-influx-init 2>&1 | tail -20; exit 1

.PHONY: wait-healthy-infra
wait-healthy-infra:  ## Block until infra services (no generator) are healthy
	@deadline=$$(( $$(date +%s) + 120 )); \
	services="captia-bms-mosquitto captia-bms-influxdb captia-bms-redis captia-bms-telegraf captia-bms-grafana captia-bms-prometheus captia-bms-loki"; \
	while [ $$(date +%s) -lt $$deadline ]; do \
	    all=true; \
	    for svc in $$services; do \
	        s=$$(docker inspect --format='{{.State.Health.Status}}' $$svc 2>/dev/null || echo missing); \
	        [ "$$s" = "healthy" ] || all=false; \
	    done; \
	    if [ "$$all" = "true" ]; then echo "==> infra healthy"; exit 0; fi; \
	    sleep 5; \
	done; \
	echo "ERROR: timeout waiting for infra healthchecks"; \
	$(COMPOSE_NOGEN) ps; exit 1

.PHONY: smoke
smoke: smoke-mqtt smoke-influx smoke-grafana smoke-schema  ## Run all post-up smoke checks

.PHONY: smoke-infra
smoke-infra: smoke-mqtt smoke-influx smoke-grafana  ## Smoke without generator HTTP (no /healthz)

.PHONY: smoke-mqtt
smoke-mqtt:
	bash scripts/smoke_mqtt.sh

.PHONY: smoke-influx
smoke-influx:
	bash scripts/smoke_influx.sh

.PHONY: smoke-grafana
smoke-grafana:
	bash scripts/smoke_grafana.sh

.PHONY: smoke-schema
smoke-schema:
	bash scripts/verify_canonical_schema.sh

.PHONY: urls
urls:  ## Print key local URLs
	@printf "Generator API : http://localhost:%s\n"  "$${BMS_GENERATOR_PORT_HOST:-8120}"
	@printf "Healthz       : http://localhost:%s/healthz\n" "$${BMS_GENERATOR_PORT_HOST:-8120}"
	@printf "Metrics       : http://localhost:%s/metrics\n" "$${BMS_GENERATOR_PORT_HOST:-8120}"
	@printf "OpenAPI docs  : http://localhost:%s/docs\n"    "$${BMS_GENERATOR_PORT_HOST:-8120}"
	@printf "InfluxDB UI   : http://localhost:%s\n"        "$${INFLUXDB_PORT_HOST:-8087}"
	@printf "Grafana       : http://localhost:%s (admin/admin by default)\n" "$${GRAFANA_PORT_HOST:-3001}"
	@printf "Prometheus    : http://localhost:%s\n"        "$${PROMETHEUS_PORT_HOST:-9090}"
	@printf "Loki          : http://localhost:%s\n"        "$${LOKI_PORT_HOST:-3100}"

# -----------------------------------------------------------------------------
# Quality gates
# -----------------------------------------------------------------------------

.PHONY: lint
lint:  ## ruff check + format check
	uv run ruff check .
	uv run ruff format --check .

.PHONY: format
format:  ## ruff format
	uv run ruff format .

.PHONY: test
test:  ## pytest -m unit
	uv run pytest -m unit -q --no-header

.PHONY: test-integration
test-integration:  ## pytest -m integration
	uv run pytest -m integration -q --no-header

.PHONY: test-snapshot
test-snapshot:  ## pytest -m snapshot
	uv run pytest -m snapshot -q --no-header

.PHONY: test-vendor
test-vendor:  ## Run the vendored synthetic-generator unit suite
	uv run pytest vendor/synthetic-generator/tests/unit -q --no-header --override-ini="markers=" -p no:cacheprovider

.PHONY: test-all
test-all: test test-integration test-snapshot test-vendor  ## All in-process test layers

.PHONY: test-e2e
test-e2e:  ## E2E smoke tests (require the stack to be running)
	uv run pytest tests/e2e -m smoke -q --no-header

# -----------------------------------------------------------------------------
# Run the FastAPI generator on the host (useful when the bms-data-generator
# container image cannot be built — e.g. registry blocked, no Docker, etc.).
# Connects to mosquitto/influxdb on their host-mapped ports.
# -----------------------------------------------------------------------------

.PHONY: run-host
run-host:  ## Run bms-data-generator on the host (uvicorn :8120)
	$(ENV_GUARD)
	BMS_MQTT_HOST=localhost \
	BMS_MQTT_PORT=$${MQTT_PORT_HOST:-1884} \
	BMS_OUTPUT_DIR=$$(pwd)/output \
	BMS_DEFAULT_CONFIG=$$(pwd)/config/projects/bms_v1_demo.yaml \
	uv run uvicorn bms_data_generator.main:app --host 0.0.0.0 --port 8120

# -----------------------------------------------------------------------------
# Dumps (Cases B / C / D)
# -----------------------------------------------------------------------------

.PHONY: dump-caseB
dump-caseB:  ## Generate Caso B dump (12-month consumption)
	bash scripts/export_dump.sh caseB

.PHONY: dump-caseC
dump-caseC:  ## Generate Caso C dump (6 months with HVAC faults)
	bash scripts/export_dump.sh caseC

.PHONY: dump-caseD
dump-caseD:  ## Generate Caso D dump (3 months IAQ at 1min)
	bash scripts/export_dump.sh caseD

# -----------------------------------------------------------------------------
# Vendor maintenance
# -----------------------------------------------------------------------------

.PHONY: vendor-update
vendor-update:  ## Re-vendor synthetic-generator from CAPTIA_CONNECT_PATH (maintainers)
	bash scripts/update_vendor.sh
