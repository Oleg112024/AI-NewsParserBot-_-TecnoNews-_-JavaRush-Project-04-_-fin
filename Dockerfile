FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Установка системных зависимостей для сборки пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаем не-root пользователя
RUN useradd -m -s /bin/bash appuser && \
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

COPY docker-requirements.txt .

RUN pip install --no-cache-dir -r docker-requirements.txt

COPY . .

# Меняем владельца для всех скопированных файлов для appuser для безопасности и предотвращения уязвимостей
RUN chown -R appuser:appuser /app

USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
