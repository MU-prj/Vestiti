# Build from the repository root: docker build -f apps/worker/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

# The workspace root is virtual: sync the worker package (and its workspace deps).
RUN uv sync --locked --no-dev --package camerino-worker

CMD ["uv", "run", "--no-sync", "arq", "camerino_worker.main.WorkerSettings"]
