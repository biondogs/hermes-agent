COMPOSE := docker compose
TWIN_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

.PHONY: build up down shell test rebase-check sync logs ps verify scan probe eval

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d
	@echo "Up: hermes-estate-twin (isolated network, no ports published)"
	@echo "Teardown: make down  (or: docker compose down -v)"

down:
	$(COMPOSE) down -v

shell:
	$(COMPOSE) exec twin bash

test:
	./scripts/twin-test

rebase-check:
	./scripts/twin-rebase-check $(REF)

sync:
	./scripts/sync-now

verify:
	./sync/verify.sh

scan:
	@echo "=== Portability scan baseline (design §5.1) ==="
	@python3 ../estate-steward/twin-tools/portability_scan.py --root $(HOME)/hermes-estate --out /tmp/portability-scan.json 2>&1 | tail -20
	@echo "--- Also scanning scripts/ ---"
	@python3 ../estate-steward/twin-tools/portability_scan.py --root $(TWIN_DIR)/../../scripts --out /tmp/portability-scan-scripts.json 2>&1 | tail -5
	@echo "Full reports: /tmp/portability-scan.json (and -scripts.json)"

probe:
	./scripts/probe-isolation.sh

eval:
	./scripts/twin-eval.sh

logs:
	$(COMPOSE) logs --tail=100 twin

ps:
	$(COMPOSE) ps -a
	docker network inspect hermes-estate-twin-internal --format '{{json .IPAM.Config}}' 2>&1 | head -5
