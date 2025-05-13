FROM python:3.10-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

FROM base AS builder

WORKDIR /app

COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv .venv \
    && .venv/bin/pip install --upgrade pip \
    && .venv/bin/pip install -r requirements.txt

COPY . .

FROM base AS final

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8080

CMD ["python", "app.py"]
