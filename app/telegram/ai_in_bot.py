from telethon import TelegramClient, events, Button
import logging
from app.utils import set_user_chat_mode, is_user_in_chat_mode, is_ai_chat_enabled
from app.ai.generator import generate_ai_chat_response, is_ai_available

logger = logging.getLogger("bot")

def register_ai_chat_handlers(client: TelegramClient):
    """
    Регистрирует обработчики для режима прямого общения с ИИ.
    """

    @client.on(events.CallbackQuery(data=b"ai_chat_start"))
    async def ai_chat_start_handler(event):
        if not is_ai_chat_enabled():
            logger.warning(f"User {event.sender_id} tried to start AI chat but it is disabled")
            await event.answer("⚠️ Чат с ИИ сейчас выключен в настройках.", alert=True)
            return

        if not is_ai_available():
            logger.warning(f"User {event.sender_id} tried to start AI chat but AI is unavailable")
            await event.answer("⚠️ ИИ сейчас недоступен. Проверьте настройки API.", alert=True)
            return

        user_id = event.sender_id
        set_user_chat_mode(user_id, True)
        logger.info(f"User {user_id} entered AI Chat mode")
        
        await event.edit(
            "💬 **Режим прямого общения с ИИ**\n\n"
            "Теперь вы можете писать любые вопросы прямо в этот чат, и ИИ ответит вам как IT-специалист.\n\n"
            "Чтобы выйти из этого режима, нажмите кнопку ниже или введите /stop.",
            buttons=[[Button.inline("⬅️ Выйти из чата", b"exit_ai_chat")]]
        )

    @client.on(events.CallbackQuery(data=b"exit_ai_chat"))
    async def exit_ai_chat_handler(event):
        user_id = event.sender_id
        set_user_chat_mode(user_id, False)
        logger.info(f"User {user_id} exited AI Chat mode via button")
        
        # Возвращаемся в меню чата
        enabled = is_ai_chat_enabled()
        status_text = "ВКЛЮЧЕН ✅" if enabled else "ВЫКЛЮЧЕН ❌"
        
        buttons = [
            [Button.inline("Выключить ИИ для чата" if enabled else "Включить ИИ для чата", b"toggle_ai_chat")],
            [Button.inline("🚀 Начать общение", b"ai_chat_start")] if enabled else [],
            [Button.inline("⬅️ Назад", b"main_menu")]
        ]
        buttons = [b for b in buttons if b]

        await event.edit(
            f"💬 **Общение с ИИ**\n\nЗдесь вы можете настроить и запустить чат с ИИ-ассистентом.\n\n"
            f"Статус чата: **{status_text}**",
            buttons=buttons
        )
        await event.answer("Вы вышли из режима чата с ИИ")

    @client.on(events.NewMessage)
    async def chat_message_handler(event):
        # Игнорируем команды
        if event.message.text.startswith('/'):
            if event.message.text == '/stop':
                user_id = event.sender_id
                if is_user_in_chat_mode(user_id):
                    set_user_chat_mode(user_id, False)
                    logger.info(f"User {user_id} exited AI Chat mode via /stop command")
                    await event.respond("Вы вышли из режима чата с ИИ.", buttons=[[Button.text("📱 Главное меню", resize=True)]])
            return

        user_id = event.sender_id
        if is_user_in_chat_mode(user_id):
            logger.info(f"User {user_id} sent message to AI: {event.message.text[:50]}...")
            # Если пользователь в режиме чата, отправляем его сообщение ИИ
            async with client.action(event.chat_id, 'typing'):
                response = await generate_ai_chat_response(event.message.text)
                logger.info(f"AI response sent to user {user_id}")
                await event.reply(response)
