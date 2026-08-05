.PHONY: help dev prod test seed down down-v logs

COMPOSE = docker compose --env-file backend/.env -f docker/docker-compose.yml
DEV = $(COMPOSE) -f docker/docker-compose.dev.yml

help:
	@echo "make dev    - levanta la API FastAPI en :8000 con reload (+ postgres)"
	@echo "make prod   - levanta la imagen de produccion (API uvicorn)"
	@echo "make test   - corre los tests en el contenedor dev"
	@echo "make seed   - puebla coffee_shops desde Geoapify (ARGS opcional)"
	@echo "make down   - para y limpia"
	@echo "make logs   - sigue los logs"

dev:
	$(DEV) up --build -d

prod:
	$(COMPOSE) up --build

test:
	$(DEV) run --rm --build -w /srv/backend app python -m pytest

seed:
	$(DEV) run --rm -w /srv/backend app python -m scripts.seed_database $(ARGS)

down:
	$(COMPOSE) down

down-v:
	$(DEV) down -v

logs:
	$(COMPOSE) logs -f
