FROM python:3.13-slim

# Запрещаем Python писать файлы .pyc на диск и включаем немедленный вывод логов
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Установка системных зависимостей
# curl нужен для healthcheck-ов в docker-compose
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/logs

# Установка зависимостей Python
COPY docker-requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r docker-requirements.txt

# Копируем проект
COPY . .

# Метаданные образа
LABEL maintainer="Oleg112024" \
      version="${APP_VERSION:-v.0.3.35AI-MENU}" \
      description="Newsbot application"

# По умолчанию запускаем API, но в docker-compose команда переопределяется для каждого сервиса
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
