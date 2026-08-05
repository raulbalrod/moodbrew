.PHONY: help dev api prod test seed down down-v logs

COMPOSE = docker compose --env-file backend/.env -f docker/docker-compose.yml
DEV = $(COMPOSE) -f docker/docker-compose.dev.yml

help:
	@echo "make dev    - levanta desarrollo con reload"
	@echo "make api    - levanta la API FastAPI en :8000 (para el front Next)"
	@echo "make prod   - levanta la imagen de produccion"
	@echo "make test   - corre los tests en el contenedor dev"
	@echo "make seed   - puebla coffee_shops desde Geoapify (ARGS opcional)"
	@echo "make down   - para y limpia"
	@echo "make logs   - sigue los logs"

dev:
	$(DEV) up --build -d

api:
	$(DEV) up --build -d api

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
