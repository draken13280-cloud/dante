FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg fonts-dejavu-core libcairo2 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini brandkits/ ./
ENV PYTHONPATH=/app/src
