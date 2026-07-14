# Build from the repository root:
#   docker build -f apps/worker/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# The uv workspace needs every member's pyproject present to resolve.
COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

RUN uv sync --frozen --no-dev --package camerino-worker

CMD ["uv", "run", "--no-sync", "arq", "camerino.worker.main.WorkerSettings"]
