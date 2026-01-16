import asyncio
from celery import Celery
from celery.schedules import crontab
from app.config import settings
from app.news_parser import collect_from_all_sources
from app.filters import filter_news
from app.utils import save_news_item, list_news_items, is_news_published, init_app_settings
from app.ai.generator import generate_telegram_post
from app.telegram.publisher import publish_to_channel
from app.schemas import Post
from app.utils import save_post
from uuid import uuid4

from app.logger import setup_logging

# Настройка логирования для Celery
logger = setup_logging("celery")

# Инициализация настроек в Redis при запуске воркера
init_app_settings()

# Инициализация Celery
celery_app = Celery(
    "tasks",
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Настройка периодических задач
celery_app.conf.beat_schedule = {
    "scrape-news-periodically": {
        "task": "app.tasks.fetch_and_store_news_task",
        "schedule": crontab(minute=f"*/{settings.news_time_call}"),
    },
    "publish-news-periodically": {
        "task": "app.tasks.publish_next_news_task",
        "schedule": crontab(minute=f"*/{settings.news_time}"),
    },
}
# Настройка часового пояса на основе UTC_OFFSET
if settings.utc_offset != 0: # При "!=0" - Бот игнорирует текстовое название TIMEZONE и просто берет число из UTC_OFFSET, или при "=0" - то использует TIMEZONE.
    # Создаем фиксированное смещение Etс/GMT (в pytz знаки инвертированы, поэтому используем -offset)
    # Например, для Москвы (+3) будет Etc/GMT-3, для Рио (-3) будет Etc/GMT+3
    offset_str = f"Etc/GMT{'+' if settings.utc_offset < 0 else '-'}{abs(settings.utc_offset)}"
    celery_app.conf.timezone = offset_str
else:
    celery_app.conf.timezone = settings.timezone

celery_app.conf.enable_utc = False # False - Используем TIMEZONE для планировщика при значении UTC_OFFSET != 0, а если True - то используем UTC по Гринвичу (для Celery).

@celery_app.task(name="app.tasks.fetch_and_store_news_task")
def fetch_and_store_news_task():
    """
    Фоновая задача для парсинга, фильтрации и сохранения новостей.
    """
    try:
        logger.info("Starting fetch_and_store_news_task...")
        news_items = collect_from_all_sources() # Парсим новости с всех источников
        logger.info(f"Collected {len(news_items)} raw items.")
        filtered_news = filter_news(news_items) # Фильтруем новости по ключевым словам
        logger.info(f"Filtered to {len(filtered_news)} items.")
        
        for item in filtered_news:
            save_news_item(item)
        
        logger.info(f"Successfully scraped and stored {len(filtered_news)} news items.")
        return f"Successfully scraped and stored {len(filtered_news)} news items."
    except Exception as e:
        logger.error(f"Error in fetch_and_store_news_task: {e}", exc_info=True)
        return f"Error: {e}"

@celery_app.task(name="app.tasks.publish_next_news_task")
def publish_next_news_task():
    """
    Берет одну неопубликованную новость, генерирует пост и публикует.
    Если уникального материала нет, запускает парсинг.
    """
    try:
        logger.info(f"Starting scheduled publication (interval: {settings.news_time} min)")
        
        # Получаем список всех новостей
        all_news = list_news_items()
        
        # Фильтруем неопубликованные
        news = None
        for item in all_news:
            if not is_news_published(item.id):
                news = item
                break
        
        if not news:
            # Если нет готовых, пробуем спарсить принудительно
            logger.info("No news in queue. Forcing immediate scrape...")
            news_list = collect_from_all_sources()
            logger.info(f"Scrape finished. Found {len(news_list)} items")
            for item in news_list:
                if not is_news_published(item.id):
                    news = item
                    break
        
        if not news:
            logger.info("Still no new unique material. Skipping publication.")
            return "No news to publish."

        logger.info(f"Processing news: {news.title[:50]}...")
        
        # Запускаем асинхронную генерацию и публикацию
        async def process_and_publish():
            generated_text = await generate_telegram_post(news)
            if generated_text:
                msg_id = await publish_to_channel(generated_text, url=news.url)
                if msg_id:
                    # Создаем объект Post для сохранения в историю
                    post = Post(
                        id=str(uuid4()),
                        news_id=news.id,
                        generated_text=generated_text,
                        status="published"
                    )
                    save_post(post)
                    logger.info(f"Successfully published: {news.title[:50]}")
                    return f"Published: {news.title}"
            return None

        result = asyncio.run(process_and_publish())
        if result:
            return result
        else:
            logger.warning(f"Failed to generate or publish post for: {news.title[:50]}")
            return "Failed to generate or publish post."
            
    except Exception as e:
        logger.error(f"Error in publish_news_task: {e}", exc_info=True)
        return f"Error: {e}"
