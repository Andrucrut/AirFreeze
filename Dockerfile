FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY .env.example .env

RUN chmod +x scripts/entrypoint.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["./scripts/entrypoint.sh"]