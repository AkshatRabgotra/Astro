FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies and curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV PORT=8000

# Using exec with sh -c allows $PORT expansion on Render, Cloud Run, or local Docker
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
