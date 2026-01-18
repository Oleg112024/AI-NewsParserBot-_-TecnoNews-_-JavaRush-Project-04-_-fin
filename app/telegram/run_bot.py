import asyncio
import logging
import sys
import os
import signal

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
    
    # Обработка SIGTERM для корректного завершения в Docker
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(client, sig)))

    # Работаем до тех пор, пока не остановят
    try:
        await client.run_until_disconnected()
    except asyncio.CancelledError:
        logger.info("Bot task cancelled.")

async def shutdown(client, sig):
    logger.info(f"Received exit signal {sig.name}...")
    await client.disconnect()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    logger.info("Cleaning up and shutting down...")
    loop = asyncio.get_running_loop()
    loop.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
