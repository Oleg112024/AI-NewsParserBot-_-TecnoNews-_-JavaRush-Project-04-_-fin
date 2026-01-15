from datetime import datetime, timezone
import logging
import hashlib
from typing import Any

from app.schemas import NewsItem
from app.utils import save_news_item, list_sources
from app.news_parser import habr, vc, tproger, three_dnews, ixbt, telegram


logger = logging.getLogger(__name__)

# Генерирует детерминированный идентификатор новости по паре (source, url).
def generate_news_id(source: str, url: str) -> str:
    base = f'{source}:{url}'

    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return digest


def normalize_raw_news(source_name: str, raw_item: dict[str, Any]) -> NewsItem:
    """
    Преобразует "сырую" новость из парсера в объект NewsItem.
    """
    source = source_name
    url = raw_item['url']
    news_id = generate_news_id(source, url)
    news_item = NewsItem(
        id=news_id,
        title=raw_item.get('title'),
        url=raw_item.get('url'),
        summary=raw_item.get('summary') or 'Нет текста',
        source=source,
        published_at=datetime.now(timezone.utc),
        keywords=[],
    )
    # print (news_item)

    return news_item



def collect_from_all_sources() -> list[NewsItem]:
    """
    Собирает новости со всех поддерживаемых источников и нормализует их в NewsItem.
    Учитывает настройки включения/выключения из Redis.
    """
    collected_news: list[NewsItem] = []
    
    # Получаем все источники из Redis
    all_sources = list_sources()
    
    # 1. Маппинг ID статических источников на функции парсинга
    site_parsers = {
        "habr": habr.fetch_habr_news_raw,
        "vc": vc.fetch_vc_news_raw,
        "tproger": tproger.fetch_tproger_news_raw,
        "3dnews": three_dnews.fetch_3dnews_news_raw,
        "ixbt": ixbt.fetch_ixbt_news_raw,
    }

    # Обработка сайтов
    for s in all_sources:
        if s.type == "site" and s.enabled and s.id in site_parsers:
            fetch_func = site_parsers[s.id]
            try:
                logger.info(f"Parsing site source: {s.id}")
                raw_items = fetch_func()
                for raw_item in raw_items:
                    try:
                        news_item = normalize_raw_news(source_name=s.id, raw_item=raw_item)
                        save_news_item(news_item)
                        collected_news.append(news_item)
                    except Exception as e:
                        logger.warning(f"Ошибка при обработке новости из {s.id}: {e}")
            except Exception as exc:
                logger.error(f'Ошибка при парсинге новостей {s.id}: {exc}')

    # 2. Обработка динамических источников (Telegram-каналы)
    tg_channels = []
    for s in all_sources:
        if s.type == "tg" and s.enabled:
            # Если это username (начинается с @), убираем его
            username = s.url.replace("https://t.me/", "").replace("@", "").strip("/")
            if username:
                tg_channels.append(username)
    
    if tg_channels:
        try:
            logger.info(f"Parsing dynamic TG channels: {tg_channels}")
            import asyncio
            # Используем asyncio.run для запуска асинхронного парсера в синхронном контексте
            raw_tg_items = asyncio.run(telegram.fetch_tg_news_raw(tg_channels))
            for raw_item in raw_tg_items:
                try:
                    news_item = normalize_raw_news(source_name=raw_item['source'], raw_item=raw_item)
                    save_news_item(news_item)
                    collected_news.append(news_item)
                except Exception as e:
                    logger.warning(f"Ошибка при нормализации новости из TG {raw_item.get('source')}: {e}")
        except Exception as exc:
            logger.error(f"Ошибка при парсинге TG каналов: {exc}")

    return collected_news
