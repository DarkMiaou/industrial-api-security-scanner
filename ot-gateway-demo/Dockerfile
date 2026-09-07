FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system gateway \
    && useradd --system --gid gateway --home-dir /app gateway

COPY ot-gateway-demo/pyproject.toml ./pyproject.toml
COPY ot-gateway-demo/app ./app

RUN pip install --no-cache-dir .

FROM base AS test

RUN pip install --no-cache-dir ".[dev]"
COPY ot-gateway-demo/tests ./tests
USER gateway

CMD ["pytest", "-p", "no:cacheprovider"]

FROM base AS runtime

USER gateway

EXPOSE 8081

HEALTHCHECK --interval=10s --timeout=3s --retries=5 --start-period=5s \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/health', timeout=2)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
