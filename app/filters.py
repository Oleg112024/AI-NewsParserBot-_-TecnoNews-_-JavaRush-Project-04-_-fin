from app.schemas import NewsItem
from app.config import settings
from app.utils import list_keywords

def filter_news(news_items: list[NewsItem]) -> list[NewsItem]:
    """
    Фильтрует список новостей по ключевым словам из настроек (.env) и из Redis.
    """
    # Собираем ключевые слова из обоих источников
    env_keywords = settings.keywords_list
    redis_keywords = list_keywords()
    
    # Объединяем и удаляем дубликаты
    all_keywords = list(set(env_keywords + redis_keywords))
    
    if not all_keywords:
        return news_items

    filtered_items = []
    for item in news_items:
        # Проверяем заголовок и описание на наличие ключевых слов
        text_to_check = f"{item.title} {item.summary}".lower()
        if any(keyword.lower() in text_to_check for keyword in all_keywords):
            filtered_items.append(item)
            
    return filtered_items
