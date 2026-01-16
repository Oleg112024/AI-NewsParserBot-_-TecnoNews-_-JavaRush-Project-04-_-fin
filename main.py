# Точка входа
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from app.config import settings
from app.api import api_router
from app.utils import save_source, get_redis_client, init_app_settings
from app.schemas import Source

from app.logger import setup_logging

# Настройка логирования
logger = setup_logging("api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при запуске
    logger.info("Starting Newsbot API...")

    # Инициализация настроек в Redis (ИИ и др.)
    init_app_settings()
    """
    Управление жизненным циклом приложения.
    Код до yield выполняется при запуске, после yield — при остановке.
    """
    # Инициализация при старте
    logger.info("Начало инициализации источников...")
    
    default_sources = [
        Source(id="habr", type="site", name="Habr новости", url="https://habr.com/ru/news/", enabled=True),
        Source(id="vc", type="site", name="VC.ru", url="https://vc.ru/", enabled=True),
        Source(id="tproger", type="site", name="Tproger", url="https://tproger.ru/", enabled=True),
        Source(id="3dnews", type="site", name="3DNews", url="https://3dnews.ru/", enabled=True),
        Source(id="ixbt", type="site", name="iXBT.com", url="https://ixbt.com/", enabled=True),
        # Каналы по умолчанию
        Source(id="habr_tg", type="tg", name="Habr TG", url="https://t.me/habr_com", enabled=True),
        Source(id="techcrunch_tg", type="tg", name="TechCrunch TG", url="https://t.me/techcrunch", enabled=True),
    ]
    
    client = get_redis_client()
    if client:
        logger.info("Подключение к Redis успешно для инициализации.")
        for source in default_sources:
            # Инициализируем только если источника еще нет в Redis
            if not client.exists(f"sources:{source.id}"):
                save_source(source)
                logger.info(f"Источник {source.id} инициализирован.")
            else:
                logger.info(f"Источник {source.id} уже существует, настройки сохранены.")
    else:
        logger.error("НЕ УДАЛОСЬ подключиться к Redis при инициализации!")
    
    logger.info("Стандартные источники инициализированы")
    logger.info("API initialized and ready to serve requests")
    
    yield
    
    # Код здесь выполнится при выключении (shutdown)
    logger.info("Приложение останавливается...")
    logger.info("Shutting down Newsbot API...")

app = FastAPI(
    title="Newsbot API",
    version="0.1.0",
    description="Newsbot API",
    debug=settings.debug,
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "message": "Hello World!",
        "debug": settings.debug,
    }

app.include_router(api_router)


if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000)

# print(settings.debug)