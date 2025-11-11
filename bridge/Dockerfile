FROM python:3.12-slim as builder

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Copy dependency files
COPY pyproject.toml ./

# Configure poetry: Don't create virtual env, install dependencies
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Production stage
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed for pyright (libatomic for Node.js) and healthcheck (curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libatomic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
# Copy all files to /app/bridge/ to maintain package structure
# Since build context is ./bridge, we copy everything to maintain the bridge package
COPY __init__.py server.py ./bridge/
COPY core/ ./bridge/core/
COPY routes/ ./bridge/routes/
COPY services/ ./bridge/services/
COPY tests/ ./bridge/tests/

EXPOSE 8787

CMD ["uvicorn", "bridge.server:app", "--host", "0.0.0.0", "--port", "8787", "--reload", "--reload-dir", "/app/bridge"]

