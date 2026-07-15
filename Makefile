.PHONY: dev down build lint typecheck test seed migrate rollback logs shell-api shell-db ci

dev:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

stop:
	docker compose stop

start:
	docker compose start

lint:
	docker compose run --rm api ruff check .

typecheck:
	docker compose run --rm api mypy app

test:
	docker compose run --rm api pytest -v

seed:
	docker compose run --rm api python scripts/seed.py

migrate:
	docker compose run --rm api alembic upgrade head

rollback:
	docker compose run --rm api alembic downgrade -1

logs:
	docker compose logs -f

shell-api:
	docker compose exec api /bin/bash

shell-db:
	docker compose exec db psql -U $${POSTGRES_USER:-valuation} -d $${POSTGRES_DB:-valuation}

# Runs the same checks as CI, useful before pushing
ci: lint typecheck test
