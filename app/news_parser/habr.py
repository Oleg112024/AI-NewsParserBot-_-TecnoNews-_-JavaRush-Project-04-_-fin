import logging
import requests
from bs4 import BeautifulSoup

from app.news_parser.sites import HABR_BASE_URL, DEFAULT_HEADERS
HABR_NEWS_URL = f"{HABR_BASE_URL}/news/"
HABR_ARTICLE_URL = f"{HABR_BASE_URL}/article/"

HABR_CARD_SELECTOR = "article.tm-articles-list__item"
HABR_TITLE_SELECTOR = "h2.tm-title.tm-title_h2"
HABR_TITLE_LINK_SELECTOR = "tm-title__link"

logger = logging.getLogger(__name__)


def parse_habr_list_html(html: str, limit: int) -> list[dict]:
    """
    Парсит HTML‑страницу списка новостей Хабра и вытаскивает ссылки на статьи.
    """
    soup = BeautifulSoup(html, "html.parser")
    news_items: list[dict] = []

    article_tags = soup.select(HABR_CARD_SELECTOR)
    if not article_tags:
        # Fallback на более общий селектор, если верстка изменилась
        article_tags = soup.find_all("article")

    for article_tag in article_tags:
        title_link = article_tag.find("a", class_=HABR_TITLE_LINK_SELECTOR)
        if not title_link:
            title_link = article_tag.find("h2").find("a") if article_tag.find("h2") else None
        
        if title_link is None:
            continue

        title_text = title_link.get_text(strip=True)
        relative_url = title_link.get('href', '')
        if relative_url is None:
            continue

        if relative_url.startswith("http"):
            full_url = relative_url
        else:
            full_url = f'https://habr.com{relative_url}'

        news_item = {
            'source': 'habr',
            'title': title_text,
            'url': full_url,
        }
        news_items.append(news_item)

    return news_items


def fetch_habr_news_raw(limit: int = 20) -> list[dict[str, str]]:
    """
    Загружает страницу новостей Хабра и возвращает список "сырых" новостей.
    """
    raw_items: list[dict[str, str]] = []

    try:
        response = requests.get(HABR_NEWS_URL, headers=DEFAULT_HEADERS, timeout=10)
    except requests.RequestException as e:
        logger.warning(f'Ошибка при парсинге новостей с хабра {e}')
        return raw_items

    if response.status_code != 200:
        logger.warning(f'При парсинге новостей с хабра  статус код - {response.status_code}')
        return raw_items

    raw_items = parse_habr_list_html(response.text, limit=limit)

    return raw_items


if __name__ == '__main__':
    pass
