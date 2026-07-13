# Indian Equity Valuation Tool (Phase 1 MVP)

Local-first DCF valuation for NSE/BSE listed companies, sourced from Screener.in.
Everything runs offline via Docker Compose — no cloud dependency.

> Sprint 1 status: project foundation only. Schema, scraper, valuation engine,
> auth, and export land in Sprints 2–6. See `Project_Plan_Phase_1.txt` for the
> full roadmap.

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- `make`

## Quickstart

```bash
cp .env.example .env
make dev        # builds images, starts db, redis, api, worker, beat
```

Once containers are healthy:

```bash
make migrate     # apply Alembic migrations (no-op until Sprint 2 adds tables)
make seed        # placeholder until Sprint 2
make test        # run pytest inside the api container
```

API docs: http://localhost:8000/docs
Health check: http://localhost:8000/health
DB connectivity check: http://localhost:8000/health/db

## Makefile targets

| Target | What it does |
|---|---|
| `make dev` | `docker compose up --build` — all five services |
| `make down` | stop and remove containers |
| `make lint` | ruff |
| `make typecheck` | mypy |
| `make test` | pytest inside the api container |
| `make migrate` | `alembic upgrade head` |
| `make rollback` | `alembic downgrade -1` |
| `make seed` | run `scripts/seed.py` |
| `make ci` | lint + typecheck + test, mirrors GitHub Actions |

## Services (docker-compose.yml)

- **db** — PostgreSQL 15, data persisted at `./data/postgres`
- **redis** — Redis 7, Celery broker + result backend
- **api** — FastAPI app, hot-reloads via volume mount
- **worker** — Celery worker (same image as api, different CMD)
- **beat** — Celery beat scheduler (same image as api, different CMD)

All services share a single `.env` file. Copy `.env.example` to `.env` before
running anything — every variable there has a safe local default, including
`SCRAPE_DELAY_SECONDS` (rate-limits Screener.in requests) and
`SCREENER_BASE_URL`.

## Screener.in scraping — ethics and limitations

Screener.in is the sole external data source for this project (see
`System_Architecture.txt`, Module 1). Scraping is implemented in Sprint 3.
Ground rules established now so later sprints don't relitigate them:

- Requests use a realistic desktop User-Agent and a configurable delay
  (`SCRAPE_DELAY_SECONDS`, default 2s) between requests.
- Celery enforces a per-task rate limit so concurrent workers can't exceed
  1 request per delay window.
- Tests and CI never hit Screener.in live — they run against saved HTML
  fixtures in `tests/fixtures/screener/`.
- Screener.in is not a real-time feed; downstream data (prices, ratios) lags
  the last scrape.

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs ruff, mypy, and pytest
against Postgres + Redis service containers on every push to `main`. CI does
not use the local Docker Compose stack.

## Project structure

```
app/
  core/          settings, celery app
  db/            async engine, session, declarative base
  models/        ORM models (Sprint 2)
  api/           routers (Sprint 3+)
  tasks.py       Celery tasks (trivial ping task for now)
  main.py        FastAPI entrypoint
alembic/         migrations
scripts/seed.py  DB seed script (placeholder until Sprint 2)
tests/           pytest suite + tests/fixtures/screener/ HTML fixtures
```
