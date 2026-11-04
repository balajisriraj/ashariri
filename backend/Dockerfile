FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app

# Dependencies first, so code changes don't reinstall them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra postgres --no-install-project

COPY ashariri ./ashariri
COPY knowledge ./knowledge
COPY persona ./persona
COPY evals ./evals
RUN uv sync --frozen --no-dev --extra postgres \
 # Bake the embedding model into the image so the first request isn't a download.
 && uv run python -c "from ashariri.embeddings import FastEmbedder; FastEmbedder().embed(['warm up'])"

RUN useradd --create-home app && chown -R app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uv", "run", "--no-sync", "ashariri", "serve", "--host", "0.0.0.0", "--port", "8000"]
