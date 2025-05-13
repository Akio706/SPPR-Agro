# syntax=docker/dockerfile:1

FROM python:3.10-slim AS base

# Install system dependencies required for Python packages (e.g., pandas, numpy, psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for running the app
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Builder stage: install dependencies in a venv
FROM base AS builder

WORKDIR /app

# Copy only requirements.txt first for better cache usage
COPY --link requirements.txt ./

# Create venv and install dependencies using pip cache
RUN python -m venv .venv \
    && .venv/bin/pip install --upgrade pip \
    && --mount=type=cache,target=/root/.cache/pip \
       .venv/bin/pip install -r requirements.txt

# Copy the rest of the application code (everything in niceGUI/)
COPY --link . .

# Final image
FROM base AS final

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
# Copy application code from builder
COPY --from=builder /app /app

# Set environment so python uses venv
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER appuser

EXPOSE 8080

CMD ["python", "app.py"]
