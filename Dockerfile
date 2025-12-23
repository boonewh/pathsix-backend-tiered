# Dockerfile for Quart + Hypercorn
FROM python:3.12-slim

WORKDIR /app

# Install PostgreSQL client tools and GPG for database backups
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m venv /venv && /venv/bin/pip install --upgrade pip && /venv/bin/pip install -r requirements.txt

COPY . .

ENV PATH="/venv/bin:$PATH"

CMD ["hypercorn", "asgi:app", "--bind", "0.0.0.0:8000"]
