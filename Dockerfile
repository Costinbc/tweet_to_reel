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

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

USER appuser

CMD exec gunicorn --chdir /app -c gunicorn_conf.py 'src.app:app'