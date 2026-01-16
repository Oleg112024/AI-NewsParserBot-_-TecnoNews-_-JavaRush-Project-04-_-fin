FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Установка системных зависимостей для сборки пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/logs

COPY docker-requirements.txt .

RUN pip install --no-cache-dir -r docker-requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
