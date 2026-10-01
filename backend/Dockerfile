FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# The lockfile pins every transitive dependency resolved from requirements.txt
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY . .

ENV PYTHONUNBUFFERED=1