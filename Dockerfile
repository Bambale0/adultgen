# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN python -m pip install --upgrade pip wheel

COPY pyproject.toml ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN python -m pip wheel --wheel-dir /wheels .

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system adultgen \
    && useradd --system --gid adultgen --home-dir /app --shell /usr/sbin/nologin adultgen

COPY --from=builder /wheels /wheels
RUN python -m pip install --no-index --find-links=/wheels adultgen \
    && rm -rf /wheels

COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

USER adultgen

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${API_PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn adultgen.apps.core_api:app --host ${API_HOST} --port ${API_PORT}"]
