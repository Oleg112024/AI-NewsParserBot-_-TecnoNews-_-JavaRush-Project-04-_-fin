import logging
from typing import Any

from app.news_parser.sites import IXBT_BASE_URL, fetch_html, parse_generic_list_html
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

# Загружает страницу новостей ixbt.com и извлекает список "сырых" новостей.
def fetch_ixbt_news_raw(limit: int = 50) -> list[dict[str, Any]]:
    try:
        html = fetch_html(IXBT_BASE_URL)
    except Exception as exc:
        logger.warning(f"Ошибка при загрузке iXBT: {exc}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    news_items = []
    
    # iXBT новости обычно лежат в блоках с классом news-list
    # или просто в списке ссылок в центральной колонке.
    # Используем более точный поиск для новостной ленты
    items = soup.select(".news-list li, .news-list-item, .item_news")
    
    if not items:
        # Если специфичные классы не найдены, используем универсальный парсер
        return parse_generic_list_html(html, "https://www.ixbt.com", "ixbt.com")

    for item in items:
        link = item.find("a")
        if not link:
            continue
            
        title = link.get_text(strip=True)
        href = link.get("href", "")
        
        if not href or len(title) < 20:
            continue
            
        if href.startswith("/"):
            full_url = f"https://www.ixbt.com{href}"
        else:
            full_url = href
            
        news_items.append({
            "source": "ixbt.com",
            "title": title,
            "url": full_url
        })
        
        if len(news_items) >= limit:
            break
            
    return news_items
