import logging
import httpx
import asyncio
from bs4 import BeautifulSoup
from typing import Any

logger = logging.getLogger(__name__)

async def fetch_tg_news_raw(channels: list[str], limit: int = 5) -> list[dict[str, Any]]:
    """
    Получает последние сообщения из списка Telegram-каналов через веб-версию (t.me/s/).
    Это не требует API ключей и работает для публичных каналов.
    """
    results = []
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        for channel_username in channels:
            try:
                url = f"https://t.me/s/{channel_username}"
                logger.info(f"Fetching news from TG web: {url}")
                
                response = await client.get(url)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch {url}: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, "html.parser")
                # Telegram web messages are in div.tgme_widget_message_wrap
                message_wraps = soup.select(".tgme_widget_message_wrap")
                
                # Берем последние limit сообщений
                for wrap in message_wraps[-limit:]:
                    msg_text_div = wrap.select_one(".tgme_widget_message_text")
                    if not msg_text_div:
                        continue
                        
                    text = msg_text_div.get_text(separator="\n").strip()
                    if len(text) < 20:
                        continue
                    
                    # Попытка найти ID сообщения для ссылки
                    msg_div = wrap.select_one(".tgme_widget_message")
                    msg_id = "0"
                    if msg_div and msg_div.has_attr("data-post"):
                        # data-post format is "channel/123"
                        msg_id = msg_div["data-post"].split("/")[-1]
                    
                    # Берем первую строку как заголовок
                    lines = text.split('\n')
                    title = lines[0][:100] if lines else "Telegram Post"
                    
                    results.append({
                        "title": title,
                        "url": f"https://t.me/{channel_username}/{msg_id}",
                        "summary": text,
                        "source": f"tg:{channel_username}",
                    })
                    
            except Exception as e:
                logger.error(f"Error fetching from channel {channel_username}: {e}")
                continue
    
    return results

def fetch_telegram_news_raw_sync() -> list[dict[str, Any]]:
    """
    Синхронная обертка для использования в общем коллекторе.
    """
    # Список каналов
    channels = ["habr_com", "techcrunch"] # Используем habr_com вместо habr
    
    try:
        return asyncio.run(fetch_tg_news_raw(channels))
    except Exception as e:
        logger.error(f"Error in fetch_telegram_news_raw_sync: {e}")
        return []
