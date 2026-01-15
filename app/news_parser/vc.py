import logging
from typing import Any

from app.news_parser.sites import VC_BASE_URL, fetch_html, parse_generic_list_html
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

# Загружает страницу новых записей vc.ru и извлекает список "сырых" новостей.
def fetch_vc_news_raw(limit: int = 50) -> list[dict[str, Any]]:
    try:
        html = fetch_html(VC_BASE_URL)
    except Exception as exc:
        logger.warning(f"Ошибка при загрузке vc.ru: {exc}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    news_items = []
    
    # VC.ru использует сложные классы, ищем заголовки в статьях
    # Обычно это селекторы вроде .content-title или ссылки внутри блоков статей
    items = soup.select(".feed__item, .content-title, .v-article")
    
    if not items:
        # Если специфичные селекторы не сработали, пробуем универсальный парсер
        return parse_generic_list_html(html, "https://vc.ru", "vc.ru")

    for item in items:
        # Ищем заголовок: это может быть сам элемент или ссылка внутри
        link = item if item.name == "a" else item.find("a", class_="content-link")
        if not link:
            link = item.find("a")
            
        if not link:
            continue
            
        title = link.get_text(strip=True)
        href = link.get("href", "")
        
        # Фильтруем слишком короткие заголовки (обычно это меню или кнопки)
        if not href or len(title) < 25:
            continue
            
        full_url = href if href.startswith("http") else f"https://vc.ru{href}"
        
        # Избегаем дублей в рамках одного парсинга
        if any(i["url"] == full_url for i in news_items):
            continue

        news_items.append({
            "source": "vc.ru",
            "title": title,
            "url": full_url
        })
        
        if len(news_items) >= limit:
            break
            
    return news_items
