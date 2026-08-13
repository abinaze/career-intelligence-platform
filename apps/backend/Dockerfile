# ── Why this file exists (read before editing) ──────────────────────────────
#
# This is a hand-synced duplicate of `infrastructure/docker/Dockerfile.backend`,
# living here specifically so PaaS providers with a single "work directory /
# root directory" monorepo setting (Koyeb) can build the backend using only
# that one setting, without needing a `../` path out of the build context.
#
# Koyeb's "Work directory" setting (see docs/setup/koyeb-setup.md) excludes
# everything outside that directory from the build environment once set —
# so pointing Work directory at `apps/backend` means the Dockerfile itself
# has to live inside `apps/backend` too, not at
# `infrastructure/docker/Dockerfile.backend`. Render's Dockerfile Path and
# Docker Build Context Directory fields are independently configurable
# (confirmed against Render's current monorepo-support docs), so Render
# doesn't strictly need this file — it could reference the canonical
# Dockerfile with a context override instead. It's used here anyway, so
# both platforms' setup guides follow the identical "Root/Work directory =
# apps/backend, Dockerfile = default" pattern rather than two different
# mental models for what is otherwise the same build.
#
# `infrastructure/docker/Dockerfile.backend` remains the canonical copy —
# it's what every docker-compose file in this repo (`docker-compose.dev.yml`,
# `docker-compose.prod.yml`, `docker-compose.oracle-vm.yml`) and the manual
# `docker build -f infrastructure/docker/Dockerfile.backend ...` command in
# `docs/deployment/guide.md` all use. If you change one, change the other —
# there is no build-time mechanism keeping them in sync, only this comment.
#
# ─────────────────────────────────────────────────────────────────────────

# ── Builder stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./

RUN uv venv /app/.venv && uv sync --no-dev

# ── Development stage ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS development

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
RUN uv venv /app/.venv && uv sync --all-extras

COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

WORKDIR /app

RUN groupadd -r appgroup && useradd -r -g appgroup appuser

COPY --from=builder /app/.venv /app/.venv

COPY --chown=appuser:appgroup . .
RUN chmod +x docker-entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Overridable so this same image works on hosts that inject their own
# port (Hugging Face Spaces, Render, Koyeb all set $PORT) without
# needing a per-host Dockerfile variant.
ENV PORT=8000

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:${PORT:-8000}/health').raise_for_status()"

ENTRYPOINT ["./docker-entrypoint.sh"]
