FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential python3-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-interaction --no-ansi --without dev --no-root

# Roda como usuário SEM privilégios: se a aplicação for comprometida, o atacante
# não é root dentro do container.
RUN useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# `exec` repassa SIGTERM ao uvicorn (encerramento limpo). Não defina
# FORWARDED_ALLOW_IPS='*': o IP do cliente é tratado em app/redis/limiter.py
# (TRUSTED_PROXY_HOPS).
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-server-header"]
