.PHONY: help dev prod test down down-v logs

COMPOSE = docker compose --env-file backend/.env -f docker/docker-compose.yml
DEV = $(COMPOSE) -f docker/docker-compose.dev.yml

help:
	@echo "make dev    - levanta desarrollo con reload"
	@echo "make prod   - levanta la imagen de produccion"
	@echo "make test   - corre los tests en el contenedor dev"
	@echo "make down   - para y limpia"
	@echo "make logs   - sigue los logs"

dev:
	$(DEV) up --build -d

prod:
	$(COMPOSE) up --build

test:
	$(DEV) run --rm --build backend pytest

down:
	$(COMPOSE) down

down-v:
	$(DEV) down -v

logs:
	$(COMPOSE) logs -f
