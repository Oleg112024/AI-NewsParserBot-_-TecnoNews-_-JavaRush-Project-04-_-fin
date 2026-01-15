import logging
from typing import Any

import requests

from app.news_parser.sites import THREEDNEWS_BASE_URL, fetch_html, parse_generic_list_html


logger = logging.getLogger(__name__)


def fetch_3dnews_news_raw(limit: int = 50) -> list[dict[str, Any]]:
    """
    Загружает главную страницу 3dnews.ru и извлекает список "сырых" новостей.
    """
    try:
        html = fetch_html(THREEDNEWS_BASE_URL)
    except requests.RequestException as exc:
        logger.warning(f"Ошибка при парсинге новостей с 3dnews.ru: {exc}")
        return []

    raw_items = parse_generic_list_html(html, THREEDNEWS_BASE_URL, "3dnews.ru")
    if limit > 0:
        raw_items = raw_items[:limit]
    return raw_items
