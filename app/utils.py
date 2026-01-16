# Вспомогательные утилиты для работы с Redis‑хранилищем новостей, постов и источников.
from __future__ import annotations

import json
import logging
from typing import Iterable

from redis import Redis
from redis.exceptions import RedisError

from app.config import settings
from app.schemas import NewsItem, Post, Source

logger = logging.getLogger("api")


def get_redis_client():
    try:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Redis at {settings.redis_url}: {e}")
        return None


def save_news_item(news: NewsItem) -> None:
    """
    Сохраняет новость в Redis и добавляет её id в множество всех новостей.
    Устанавливает TTL из настроек TIME_LIFE_NEWS. И исключает повторение публикации новости.
    """
    client = get_redis_client()
    if client is None:
        return
    
    # 1. Защита от дублей: проверяем, нет ли уже этой новости в базе или в списке опубликованных
    if is_news_exists(news.id) or is_news_published(news.id):
        return

    key = f"news:{news.id}"
    try:
        # 2. Сохраняем новость с TTL из настроек
        client.set(key, news.model_dump_json(), ex=settings.time_life_news)
        # 3. Добавляем в множество (SADD гарантирует уникальность ID в списке)
        client.sadd("news:ids", news.id)
    except RedisError as e:
        logger.error(f"Redis error in save_news_item: {e}")
        return


def is_news_exists(news_id: str) -> bool:
    """
    Проверяет существование новости в Redis по её ID.
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        return client.exists(f"news:{news_id}") > 0
    except RedisError as e:
        logger.error(f"Redis error in is_news_exists: {e}")
        return False


def get_news_item(news_id: str) -> NewsItem | None:
    """
    Возвращает новость по id из Redis или None, если её нет/произошла ошибка.
    """
    client = get_redis_client()
    if client is None:
        return None
    try:
        raw = client.get(f"news:{news_id}")
    except RedisError as e:
        logger.error(f"Redis error in get_news_item: {e}")
        return None
    if raw is None:
        return None
    data = json.loads(raw)
    return NewsItem.model_validate(data)


def list_news_items(limit: int | None = None) -> list[NewsItem]:
    """
    Возвращает список новостей из Redis, не более limit штук (если задан)
    или не более settings.max_news_items по умолчанию.
    """
    client = get_redis_client()
    if client is None:
        return []
    
    # Если лимит не передан в функцию, берем его из настроек
    effective_limit = limit if limit is not None else settings.max_news_items
    
    try:
        ids: Iterable[str] = client.smembers("news:ids")
    except RedisError as e:
        logger.error(f"Redis error in list_news_items (smembers): {e}")
        return []
    
    result: list[NewsItem] = []
    for news_id in ids:
        item = get_news_item(news_id)
        if item is not None:
            result.append(item)
            if len(result) >= effective_limit:
                break
        else:
            # Если новости по ID нет (удалилась по TTL), удаляем ID из индекса
            try:
                client.srem("news:ids", news_id)
            except RedisError:
                pass
    return result


def save_post(post: Post) -> None:
    """
    Сохраняет пост в Redis и добавляет его id в множество всех постов.
    """
    client = get_redis_client()
    if client is None:
        return
    key = f"posts:{post.id}"
    try:
        client.set(key, post.model_dump_json())
        client.sadd("posts:all", post.id)
        client.sadd("published_news:ids", post.news_id)
    except RedisError as e:
        logger.error(f"Redis error in save_post: {e}")
        return


def is_news_published(news_id: str) -> bool:
    client = get_redis_client()
    if client is None:
        return False
    try:
        return client.sismember("published_news:ids", news_id)
    except RedisError as e:
        logger.error(f"Redis error in is_news_published: {e}")
        return False


def get_post(post_id: str) -> Post | None:
    """
    Возвращает пост по id из Redis или None при отсутствии/ошибке.
    """
    client = get_redis_client()
    if client is None:
        return None
    try:
        raw = client.get(f"posts:{post_id}")
    except RedisError as e:
        logger.error(f"Redis error in get_post: {e}")
        return None
    if raw is None:
        return None
    data = json.loads(raw)
    return Post.model_validate(data)


def save_source(source: Source) -> None:
    """
    Сохраняет источник новостей в Redis и добавляет его id в множество источников.
    """
    client = get_redis_client()
    if client is None:
        return
    key = f"sources:{source.id}"
    try:
        client.set(key, source.model_dump_json())
        client.sadd("sources:all", source.id)
    except RedisError as e:
        logger.error(f"Redis error in save_source: {e}")
        return


def list_sources() -> list[Source]:
    """
    Возвращает список всех источников из Redis.
    """
    client = get_redis_client()
    if client is None:
        return []
    try:
        # Получаем все ключи, начинающиеся с 'sources:' или 'source:'
        source_keys = client.keys("sources:*")
        old_source_keys = client.keys("source:*")
        
        # Фильтруем системный ключ sources:all из списка ключей данных
        keys = [k for k in source_keys if k != "sources:all"] + old_source_keys
        
        result = []
        seen_ids = set()
        
        for key in keys:
            raw = client.get(key)
            if raw:
                try:
                    data = json.loads(raw)
                    source = Source.model_validate(data)
                    if source.id not in seen_ids:
                        result.append(source)
                        seen_ids.add(source.id)
                except Exception as e:
                    logger.warning(f"Ошибка валидации источника из ключа {key}: {e}")
                    continue
        return result
    except RedisError as e:
        logger.error(f"Redis error in list_sources: {e}")
        return []


def delete_source(source_id: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.delete(f"sources:{source_id}")
        client.delete(f"source:{source_id}")
        client.srem("sources:all", source_id)
    except RedisError:
        pass


def add_keyword(word: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.sadd("keywords:all", word)
    except RedisError:
        pass


def list_keywords() -> list[str]:
    client = get_redis_client()
    if client is None:
        return []
    try:
        return list(client.smembers("keywords:all"))
    except RedisError:
        return []


def delete_keyword(word: str) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.srem("keywords:all", word)
    except RedisError:
        pass


def set_ai_setting(value: str) -> None:
    """Устанавливает глобальную настройку ИИ (on/off) в Redis."""
    client = get_redis_client()
    if client:
        client.set("settings:ai_agent", value.lower())


def set_user_chat_mode(user_id: int, enabled: bool) -> None:
    """Устанавливает режим чата с ИИ для конкретного пользователя."""
    client = get_redis_client()
    if client:
        key = f"user:{user_id}:chat_mode"
        if enabled:
            client.set(key, "on", ex=3600)  # Режим чата активен 1 час
        else:
            client.delete(key)


def is_user_in_chat_mode(user_id: int) -> bool:
    """Проверяет, находится ли пользователь в режиме чата с ИИ."""
    client = get_redis_client()
    if client:
        return client.exists(f"user:{user_id}:chat_mode") > 0
    return False


def set_ai_chat_enabled(enabled: bool) -> None:
    """Устанавливает глобальную настройку доступности чата с ИИ (не влияет на новости)."""
    client = get_redis_client()
    if client:
        client.set("settings:ai_chat_enabled", "on" if enabled else "off")


def is_ai_chat_enabled() -> bool:
    """Проверяет, включен ли функционал чата с ИИ."""
    client = get_redis_client()
    if client:
        val = client.get("settings:ai_chat_enabled")
        return val != "off"  # По умолчанию включен
    return True


def get_ai_setting() -> str:
    """Возвращает текущую настройку ИИ (по умолчанию берет из settings.ai_agent)."""
    client = get_redis_client()
    if client:
        val = client.get("settings:ai_agent")
        if val:
            return val
    return settings.ai_agent.lower()


def toggle_source_enabled(source_id: str) -> bool:
    """Переключает статус включения источника и возвращает новый статус."""
    client = get_redis_client()
    if not client:
        return False
    
    source_key = f"sources:{source_id}"
    raw = client.get(source_key)
    if not raw:
        return False
    
    data = json.loads(raw)
    data["enabled"] = not data.get("enabled", True)
    client.set(source_key, json.dumps(data))
    return data["enabled"]


def init_app_settings():
    """Инициализирует базовые настройки в Redis при запуске, если они отсутствуют."""
    client = get_redis_client()
    if client:
        logger.info("Successfully connected to Redis. Initializing settings...")
        if not client.exists("settings:ai_agent"):
            # По умолчанию включаем ИИ, если он не был настроен ранее
            client.set("settings:ai_agent", "on")
            logger.info("AI setting initialized to ON")
        
        # Проверяем текущее состояние для лога
        ai_status = client.get("settings:ai_agent")
        logger.info(f"AI settings initialized to {ai_status.upper()} (available)")
    else:
        logger.error("Could not initialize app settings: Redis is unavailable")


def get_source(source_id: str) -> Source | None:
    """
    Возвращает источник по id из Redis или None при отсутствии/ошибке.
    """
    client = get_redis_client()
    if client is None:
        return None
    try:
        raw = client.get(f"sources:{source_id}")
    except RedisError:
        return None
    if raw is None:
        return None
    data = json.loads(raw)
    return Source.model_validate(data)
