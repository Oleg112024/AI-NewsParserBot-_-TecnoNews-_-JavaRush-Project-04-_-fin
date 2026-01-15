""" Маршруты для FastAPI """
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.schemas import NewsItem, Post, Source, Keywords
from app.news_parser import collect_from_all_sources
from app.utils import (
    list_news_items, 
    get_news_item, 
    save_post, 
    add_keyword, 
    list_keywords, 
    delete_keyword, 
    save_source, 
    list_sources, 
    delete_source,
    get_post,
    get_redis_client
)
from app.telegram.publisher import publish_to_channel
from app.ai.generator import generate_telegram_post
from app.filters import filter_news


from app.tasks import fetch_and_store_news_task, publish_next_news_task

api_router = APIRouter()

# Эндпоинт "/news/publish"
@api_router.get("/news/publish")
async def manual_publish():
    """
    Принудительно запускает задачу публикации следующей новости.
    """
    result = publish_next_news_task.delay()
    return {"status": "Task queued", "task_id": result.id}

# Эндпоинт "/news/scrape-task"
@api_router.get("/news/scrape-task")
async def manual_scrape():
    """
    Принудительно запускает задачу сбора новостей в фоновом режиме.
    """
    result = fetch_and_store_news_task.delay()
    return {"status": "Task queued", "task_id": result.id}


# Эндпоинт "/health"
@api_router.get("/health")
async def health():
    """
    Простой health‑чек для проверки, что API запущен.
    """
    return {"status": "ok"}

# Эндпоинт "/news"
@api_router.get("/news", response_model=list[NewsItem])
async def news_list(limit: int | None = None) -> list[NewsItem]:
    return list_news_items(limit=limit)


# Эндпоинт "/news/scrape"
@api_router.get("/news/scrape", response_model=list[NewsItem])
async def scrape_news():
    """
    Запускает парсер новостей со всех источников, фильтрует их и возвращает актуальный список.
    """
    news_items = collect_from_all_sources()
    filtered_news = filter_news(news_items)
    return filtered_news


# Эндпоинт "/news/{news_id}/publish"
@api_router.post("/news/{news_id}/publish", response_model=Post)
async def publish_news(news_id: str) -> Post:
    """
    Публикует выбранную новость в Telegram‑канал и сохраняет информацию о посте.
    """
    news = get_news_item(news_id)
    if news is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Новость не найдена в хранилище",
        )

    # Генерируем текст поста через AI
    text = await generate_telegram_post(news)

    try:
        message_id = await publish_to_channel(text, url=str(news.url))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка при отправке сообщения в Telegram: {exc}",
        )

    post = Post(
        id=str(uuid4()),
        news_id=news.id,
        generated_text=text,
        published_at=news.published_at,
        status="published",
    )
    save_post(post)
    return post


@api_router.get("/posts", response_model=list[Post])
async def list_published_posts():
    """
    Возвращает историю опубликованных постов.
    """
    client = get_redis_client()
    if client is None:
        return []
    ids = client.smembers("posts:all")
    posts = []
    for pid in ids:
        p = get_post(pid)
        if p:
            posts.append(p)
    return posts


# --- Управление источниками ---

@api_router.get("/sources", response_model=list[Source])
async def sources_list():
    return list_sources()


@api_router.post("/sources", response_model=Source)
async def add_new_source(source: Source):
    save_source(source)
    return source


@api_router.delete("/sources/{source_id}")
async def remove_source(source_id: str):
    delete_source(source_id)
    return {"status": "deleted"}


# --- Управление ключевыми словами ---

@api_router.get("/keywords", response_model=list[str])
async def keywords_list_api():
    return list_keywords()


@api_router.post("/keywords")
async def add_new_keyword(keyword: str):
    add_keyword(keyword)
    return {"keyword": keyword, "status": "added"}


@api_router.delete("/keywords/{keyword}")
async def remove_keyword(keyword: str):
    delete_keyword(keyword)
    return {"status": "deleted"}


@api_router.post("/news/{news_id}/generate", response_model=dict)
async def generate_only(news_id: str):
    """
    Генерирует текст поста без публикации (для теста).
    """
    news = get_news_item(news_id)
    if news is None:
        raise HTTPException(status_code=404, detail="News not found")
    
    text = await generate_telegram_post(news)
    return {"news_id": news_id, "generated_text": text}
