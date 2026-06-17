# Single image used for BOTH local (docker compose) and Railway — full parity.
FROM python:3.11-slim

# WeasyPrint runtime libraries (Pango / Cairo / GDK-Pixbuf) + fonts.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libcairo2 libffi-dev fonts-liberation \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persist SQLite outside the image layer (Railway volume mounts here).
ENV RAILWAY_DATABASE_PATH=/data/portal.db
RUN mkdir -p /data

EXPOSE 8000
# Railway provides $PORT; default 8000 locally.
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --timeout 120 --workers 2"]
