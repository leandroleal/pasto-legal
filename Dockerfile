FROM python:3.12-slim

# 1. Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. System dependencies
RUN apt-get update && apt-get -y install libpq-dev gcc git htop curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

# 3. Copy ONLY the dependency files first (for better caching)
COPY pyproject.toml uv.lock ./

# 4. Install dependencies 
# --frozen: ignores pyproject.toml updates
# --no-install-project: skips installing your actual app code in this layer
RUN uv sync --frozen --no-cache --no-install-project

# 5. Copy the rest of application
COPY . .

# 6. Final sync to install the project itself
RUN uv sync --frozen --no-cache
