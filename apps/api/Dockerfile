# Build from the repository root:
#   docker build -f apps/api/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# The uv workspace needs every member's pyproject present to resolve.
COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

RUN uv sync --frozen --no-dev --package camerino-api

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "camerino.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
