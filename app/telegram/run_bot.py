import asyncio
import logging
import sys
import os

# Добавляем корневую директорию проекта в sys.path, чтобы импорты 'app.*' работали
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.telegram.bot import get_telegram_client, start_bot

from app.logger import setup_logging

# Настройка логирования
logger = setup_logging("bot")

async def main():
    logger.info("Starting Telegram Bot in listening mode...")
    
    # Создаем клиент. Используем имя сессии по умолчанию, чтобы сохранять авторизацию.
    client = get_telegram_client(session_name="newsbot_interactive")
    
    # Запускаем бота (авторизация + команды меню)
    await start_bot(client)
    
    logger.info("Bot is authorized and listening for messages.")
    
    # Работаем до тех пор, пока не остановят
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
