# syntax=docker/dockerfile:1
# Pin the base image by digest before you rely on this in production;
# Dependabot (.github/dependabot.yml) proposes digest updates.
FROM python:3.15-slim-bookworm AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --require-hashes --no-deps -r requirements.txt

FROM python:3.15-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
RUN groupadd --system --gid 10001 app && useradd --system --uid 10001 --gid app --no-create-home app
WORKDIR /srv
COPY --from=build /opt/venv /opt/venv
COPY --chown=root:root app ./app
COPY --chown=root:root openapi.json ./openapi.json
USER 10001
EXPOSE 8080
HEALTHCHECK NONE
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--no-server-header"]
