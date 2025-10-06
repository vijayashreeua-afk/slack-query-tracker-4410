FROM python:3.11-slim as base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# App code
COPY . .

# Data directory for JSON storage
RUN mkdir -p /app/data

ENV PORT=5000
EXPOSE 5000

# Healthcheck (expects 200 from /api/config/channel or add /api/health)
HEALTHCHECK --interval=30s --timeout=5s CMD curl -fsS http://localhost:$PORT/api/config/channel || exit 0

# Run via gunicorn
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "app:app"]
