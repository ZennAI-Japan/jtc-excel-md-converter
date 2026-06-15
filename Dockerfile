FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir '.[pdf]' \
    && mkdir -p /work/outputs \
    && chown -R app:app /work /app

WORKDIR /work
USER app

ENTRYPOINT ["jtc-md-convert"]
CMD ["--help"]
