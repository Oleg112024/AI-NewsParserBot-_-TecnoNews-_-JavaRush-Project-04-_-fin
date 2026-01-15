from __future__ import annotations
from telethon import TelegramClient, events, Button, functions, types
import logging
from app.config import settings
from app.utils import (
    list_sources, toggle_source_enabled, get_ai_setting, set_ai_setting, 
    init_app_settings, is_ai_chat_enabled, set_ai_chat_enabled
)
from app.ai.generator import is_ai_available


from app.telegram.ai_in_bot import register_ai_chat_handlers

logger = logging.getLogger("bot")

# Регистрация обработчиков событий
def register_handlers(client: TelegramClient):
    @client.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        logger.info(f"User {event.sender_id} requested /start")
        # Отправляем сообщение с Inline-кнопками и добавляем обычную кнопку меню (ReplyKeyboard)
        await event.respond(
            "📱 **Меню управления NewsBot**\n\nВыберите раздел для настройки:",
            buttons=[
                [Button.inline("🔧 Работа с новостями", b"news_work_menu")],
                [Button.inline("💬 Общение с ИИ", b"ai_chat_main_menu")]
            ]
        )
        
        await event.respond(
            "Вы можете вызвать это меню* в любой момент кнопкой ниже или командой /start \n\n*тестовый режим для администратора",
            buttons=[[Button.text("📱 Главное меню", resize=True)]]
        )

    @client.on(events.NewMessage(pattern='📱 Главное меню'))
    async def main_menu_text_handler(event):
        logger.info(f"User {event.sender_id} clicked Main Menu button")
        await start_handler(event)

    @client.on(events.CallbackQuery(data=b"news_work_menu"))
    async def news_work_menu_handler(event):
        logger.info(f"User {event.sender_id} opened News Work menu")
        await event.edit(
            "🔧 **Работа с новостями**\n\nВыберите опцию для настройки сбора и обработки новостей:",
            buttons=[
                [Button.inline("🔍 Источники для сбора новостей", b"sources_menu")],
                [Button.inline("🤖 Настройка ИИ (коррекция)", b"ai_menu")],
                [Button.inline("⬅️ Назад", b"main_menu")]
            ]
        )

    @client.on(events.CallbackQuery(data=b"sources_menu"))
    async def sources_menu_handler(event):
        logger.info(f"User {event.sender_id} opened Sources menu")
        sources = list_sources()
        buttons = []
        for s in sources:
            status = "✅" if s.enabled else "❌"
            buttons.append([Button.inline(f"{status} {s.name}", f"toggle_src_{s.id}")])
        
        buttons.append([Button.inline("⬅️ Назад", b"news_work_menu")])
        await event.edit("📡 **Выбор источников новостей**\n\nНажмите на источник, чтобы включить/выключить его:", buttons=buttons)

    @client.on(events.CallbackQuery(data=b"ai_menu"))
    async def ai_menu_handler(event):
        logger.info(f"User {event.sender_id} opened AI correction menu")
        current_status = get_ai_setting()
        ai_ready = is_ai_available()
        
        status_text = "ВКЛЮЧЕН ✅" if current_status == "on" else "ВЫКЛЮЧЕН ❌"
        if not ai_ready:
            status_text += "\n⚠️ **ИИ недоступен (проверьте API ключи)**"
        
        on_label = "Включить ON"
        if not ai_ready:
            on_label = "🚫 ON (Недоступно)"
        
        buttons = [
            [
                Button.inline(on_label if current_status == "off" else "✅ ON", b"set_ai_on"),
                Button.inline("ВЫКЛЮЧИТЬ OFF" if current_status == "on" else "✅ OFF", b"set_ai_off")
            ],
            [Button.inline("⬅️ Назад", b"news_work_menu")]
        ]
        await event.edit(f"🤖 **Настройка ИИ-коррекции**\n\nТекущий статус: **{status_text}**", buttons=buttons)

    @client.on(events.CallbackQuery(data=b"ai_chat_main_menu"))
    async def ai_chat_main_menu_handler(event):
        logger.info(f"User {event.sender_id} opened AI Chat menu")
        enabled = is_ai_chat_enabled()
        status_text = "ВКЛЮЧЕН ✅" if enabled else "ВЫКЛЮЧЕН ❌"
        
        buttons = [
            [Button.inline("Выключить ИИ для чата" if enabled else "Включить ИИ для чата", b"toggle_ai_chat")],
            [Button.inline("🚀 Начать общение", b"ai_chat_start")] if enabled else [],
            [Button.inline("⬅️ Назад", b"main_menu")]
        ]
        # Фильтруем пустые списки кнопок
        buttons = [b for b in buttons if b]
        
        await event.edit(
            f"💬 **Общение с ИИ**\n\nЗдесь вы можете настроить и запустить чат с ИИ-ассистентом.\n\n"
            f"Статус чата: **{status_text}**",
            buttons=buttons
        )

    @client.on(events.CallbackQuery(data=b"toggle_ai_chat"))
    async def toggle_ai_chat_handler(event):
        current = is_ai_chat_enabled()
        set_ai_chat_enabled(not current)
        logger.info(f"User {event.sender_id} toggled AI Chat to {'OFF' if current else 'ON'}")
        await ai_chat_main_menu_handler(event)
        await event.answer(f"Чат с ИИ {'выключен' if current else 'включен'}")

    @client.on(events.CallbackQuery(data=b"main_menu"))
    async def main_menu_handler(event):
        logger.info(f"User {event.sender_id} returned to Main Menu")
        await event.edit(
            "📱 **Меню управления NewsBot**\n\nВыберите раздел для настройки:",
            buttons=[
                [Button.inline("🔧 Работа с новостями", b"news_work_menu")],
                [Button.inline("💬 Общение с ИИ", b"ai_chat_main_menu")]
            ]
        )

    # Регистрация дополнительных обработчиков (чат с ИИ)
    register_ai_chat_handlers(client)

    @client.on(events.CallbackQuery(pattern=b"toggle_src_"))
    async def toggle_source_handler(event):
        source_id = event.data.decode().replace("toggle_src_", "")
        new_status = toggle_source_enabled(source_id)
        logger.info(f"User {event.sender_id} toggled source {source_id} to {'ON' if new_status else 'OFF'}")
        await sources_menu_handler(event)
        await event.answer(f"Источник {'включен' if new_status else 'выключен'}")

    @client.on(events.CallbackQuery(data=b"set_ai_on"))
    async def set_ai_on_handler(event):
        if not is_ai_available():
            logger.warning(f"User {event.sender_id} tried to enable AI but it's unavailable")
            await event.answer("⚠️ ИИ недоступен! Проверьте API ключи в .env", alert=True)
            return
        set_ai_setting("on")
        logger.info(f"User {event.sender_id} enabled AI correction")
        await ai_menu_handler(event)
        await event.answer("ИИ активирован ✅")

    @client.on(events.CallbackQuery(data=b"set_ai_off"))
    async def set_ai_off_handler(event):
        set_ai_setting("off")
        logger.info(f"User {event.sender_id} disabled AI correction")
        await ai_menu_handler(event)
        await event.answer("ИИ деактивирован ❌")


# Создание экземпляра TelegramClient
def get_telegram_client(session_name: str = "newsbot_session") -> TelegramClient:
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        raise RuntimeError("Telegram API credentials are not configured")

    client = TelegramClient(
        session_name,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )
    
    register_handlers(client)
    return client


# Запуск бота
async def start_bot(client: TelegramClient) -> TelegramClient:
    # Инициализация настроек (ИИ и др.)
    init_app_settings()
    
    if not settings.telegram_bot_token:
        raise RuntimeError("Telegram bot token is not configured")
    if not client.is_connected():
        await client.start(bot_token=settings.telegram_bot_token)
    
    # Установка команд бота для появления кнопки "Меню"
    try:
        await client(functions.bots.SetBotCommandsRequest(
            scope=types.BotCommandScopeDefault(),
            lang_code='',
            commands=[
                types.BotCommand(command='start', description='Открыть меню управления')
            ]
        ))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to set bot commands: {e}")
        
    return client
