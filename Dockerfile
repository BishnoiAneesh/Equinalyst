FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
# Install project + dev deps; no lockfile yet in Sprint 1, pin later if reproducibility matters
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

COPY . .

# Default CMD is overridden per-service in docker-compose.yml (api/worker/beat)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
