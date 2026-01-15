import logging
from typing import Any

import requests
from bs4 import BeautifulSoup


# Базовые URL сайтов, которые нужно парсить по ТЗ
HABR_BASE_URL = "https://habr.com/ru"
VC_BASE_URL = "https://vc.ru/new"
TPROGER_BASE_URL = "https://tproger.ru"
THREEDNEWS_BASE_URL = "https://3dnews.ru"
IXBT_BASE_URL = "https://www.ixbt.com/news/"


DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


logger = logging.getLogger(__name__)


def fetch_html(url: str) -> str:
    """
    Загружает HTML-страницу по указанному URL с базовыми заголовками.
    """
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
    response.raise_for_status()
    return response.text


def parse_generic_list_html(html: str, base_url: str, source_name: str, min_title_length: int = 20) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    news_items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a"):
        href = (link.get("href") or "").strip()
        text = link.get_text(strip=True)

        if not href or not text:
            continue

        # Собираем абсолютный URL для относительных ссылок
        if href.startswith("/"):
            full_url = f"{base_url}{href}"
        elif href.startswith(base_url):
            full_url = href
        else:
            # Ссылки на другие домены нас не интересуют
            continue

        # Отбрасываем слишком короткие заголовки (скорее всего это меню/служебные ссылки)
        if len(text) < min_title_length:
            continue

        if full_url in seen_urls:
            continue

        seen_urls.add(full_url)
        news_items.append(
            {
                "source": source_name,
                "title": text,
                "url": full_url,
            }
        )

    return news_items
