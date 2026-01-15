import logging
from app.schemas import NewsItem
from app.config import settings
from app.ai.openai_client import generate_text_openai
from app.ai.groqai_client import generate_text_groq
from app.ai.deepseek_client import generate_text_deepseek

from app.utils import get_ai_setting

logger = logging.getLogger(__name__)

def is_ai_available() -> bool:
    """
    Проверяет доступность ИИ провайдера (наличие API ключа).
    """
    provider = settings.ai_provider.lower()
    if provider == "openai":
        return bool(settings.openai_api_key)
    elif provider == "deepseek":
        return bool(settings.deepseek_api_key)
    elif provider == "groq":
        return bool(settings.groq_api_key)
    return False

async def generate_text(prompt: str, system_message: str = "You are a helpful assistant.", bypass_news_setting: bool = False) -> str | None:
    """
    Диспетчер для выбора AI провайдера на основе настроек.
    """
    # Проверяем настройку из Redis вместо статического .env
    # Если bypass_news_setting=True, значит это запрос из чата, и мы не смотрим на общую настройку ИИ для новостей
    if not bypass_news_setting and get_ai_setting() == "off":
        logger.warning("AI Agent is disabled. Skipping AI generation.")
        return None

    provider = settings.ai_provider.lower()
    if provider == "openai":
        return await generate_text_openai(prompt, system_message)
    elif provider == "deepseek":
        return await generate_text_deepseek(prompt, system_message)
    else:
        # Groq по умолчанию
        return await generate_text_groq(prompt, system_message)

async def generate_telegram_post(news: NewsItem) -> str:
    """
    Генерирует текст поста для Telegram на основе новости.
    Использует ИИ, если он включен, иначе возвращает стандартное форматирование.
    """
    system_message = (
        "Ты — профессиональный SMM-менеджер новостного IT-канала."
        "Твоя задача — писать короткие, вовлекающие и информативные посты для Telegram на русском языке. "
        "Используй подходящие emoji, структурируй текст и добавь призыв к действию (Call to Action)."
    )
    
    prompt = (
        f"Напиши пост для Telegram на основе следующей новости:\n\n"
        f"Заголовок: {news.title}\n"
        f"Источник: {news.source}\n"
        f"Описание: {news.summary}\n\n"
        f"Ссылка: {news.url}\n\n"
        f"Требования к посту:\n"
        f"1. Краткость (не более 500 символов).\n"
        f"2. Привлекательный заголовок.\n"
        f"3. Ссылка на оригинал в конце.\n"
        f"4. Несколько подходящих эмодзи.\n"
        f"5. Тон: профессиональный, но дружелюбный."
    )
    
    generated_text = await generate_text(prompt, system_message)
    
    # Если ИИ вернул текст, используем его и добавляем пометку с указанием провайдера
    if generated_text:
        provider_display = {
            "openai": "OpenAI",
            "groq": "Groq",
            "deepseek": "DeepSeek"
        }.get(settings.ai_provider.lower(), settings.ai_provider.capitalize())
        
        return f"🤖 [ИИ] ({provider_display})\n\n{generated_text}"
        
    # Fallback механизм: стандартное форматирование с пометкой [Original]
    return (
        f"📝 [Original]\n\n"
        f"📢 {news.title}\n\n"
        f"{news.summary}\n\n"
        f"🔗 Источник: {news.source}\n"
        f"👉 Читать полностью: {news.url}"
    )

async def generate_ai_chat_response(user_message: str) -> str:
    """
    Генерирует ответ ИИ на сообщение пользователя в режиме чата.
    """
    system_message = (
        "Ты — опытный IT-специалист и аналитик новостей."
        "Твоя задача — отвечать на вопросы пользователя профессионально, четко и по делу."
        "Ты можешь обсуждать технологии, программирование, новости IT и помогать с решением технических вопросов."
        "Отвечай на русском языке, используй дружелюбный, но деловой тон."
    )
    
    response = await generate_text(user_message, system_message, bypass_news_setting=True)
    
    if not response:
        return "⚠️ Извините, я сейчас не могу ответить. Попробуйте позже или проверьте настройки ИИ."
        
    return response
