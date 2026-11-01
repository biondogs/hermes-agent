COMPOSE := docker compose
TWIN_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

.PHONY: build up down shell test rebase-check sync logs ps verify scan probe

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
	./sync/scan.sh

probe:
	./scripts/probe-isolation.sh

logs:
	$(COMPOSE) logs --tail=100 twin

ps:
	$(COMPOSE) ps -a
	docker network inspect hermes-estate-twin-internal --format '{{json .IPAM.Config}}' 2>&1 | head -5
