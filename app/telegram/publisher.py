from __future__ import annotations

from typing import Optional, Any

from telethon import Button
from telethon.errors import RPCError

from app.config import settings
from app.telegram.bot import get_telegram_client


import logging

logger = logging.getLogger(__name__)

async def publish_to_channel(text: str, url: Optional[str | Any] = None, channel_id: Optional[str] = None) -> str:
    """
    Публикует сообщение в канал. Если передан url, добавляет кнопку-ссылку на источник.
    Также добавляет кнопку перехода в бота для настройки.
    """
    # Преобразуем URL в строку, если передан объект (например, AnyHttpUrl от Pydantic)
    if url is not None:
        url = str(url)
    
    # Создаем новый клиент для каждой публикации
    client = get_telegram_client(session_name=":memory:") 
    
    target = channel_id or settings.telegram_channel_id
    if not target:
        raise RuntimeError("Telegram channel id is not configured")
    
    logger.info(f"Publishing to channel {target}...")
    try:
        await client.start(bot_token=settings.telegram_bot_token)
        async with client:
            # Получаем информацию о боте, чтобы сформировать ссылку на него
            me = await client.get_me()
            bot_username = me.username
            
            buttons = []
            row = []
            
            # 1. Кнопка перехода к источнику
            if url:
                row.append(Button.url("🔗 Читать в источнике", url))
            
            # 2. Кнопка управления (ссылка на бота)
            row.append(Button.url("⚙️ Настроить бота", f"https://t.me/{bot_username}"))
            
            if row:
                buttons.append(row)

            # Попытка получить сущность (канал/чат) перед отправкой для более точной диагностики
            try:
                # Если target - это юзернейм без @, добавляем его
                if isinstance(target, str) and not target.startswith('@') and not target.replace('-', '').isdigit():
                    target = f"@{target}"
                
                entity = await client.get_entity(target)
                logger.info(f"Target resolved: {type(entity).__name__} (ID: {entity.id})")
            except Exception as e:
                logger.error(f"Failed to resolve target '{target}': {e}")
                raise RuntimeError(
                    f"Не удалось найти канал/чат '{target}'.\n"
                    f"1. Убедитесь, что бот добавлен в канал как администратор.\n"
                    f"2. Проверьте правильность юзернейма в .env (должен начинаться с @).\n"
                    f"3. Если канал приватный, используйте его числовой ID.\n"
                    f"Техническая ошибка: {e}"
                )

            message = await client.send_message(entity, text, buttons=buttons if buttons else None)
            logger.info(f"Successfully published message {message.id}")
            return str(message.id)
    except RPCError as exc:
        logger.error(f"Telegram RPC error: {exc}")
        raise RuntimeError(f"Failed to send message to Telegram: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error during publication: {exc}")
        raise exc
