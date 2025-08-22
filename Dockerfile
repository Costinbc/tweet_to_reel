FROM node:20-alpine AS ui
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY tailwind.config.js ./
COPY static ./static
COPY templates ./templates
RUN npm run build:css

FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app
COPY --from=ui /app/static/styles.css /app/static/styles.css
RUN mkdir -p /app/downloads /app/results && chown -R appuser:appuser /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080

USER appuser

CMD ["/bin/sh","-c","exec gunicorn -c gunicorn_conf.py"]