import logging
from groq import AsyncGroq
from app.config import settings

logger = logging.getLogger(__name__)

async def generate_text_groq(prompt: str, system_message: str = "You are a helpful assistant.") -> str | None:
    """
    Генерирует текст с помощью Groq AI, используя параметры из примера (reasoning_effort, streaming).
    """
    if not settings.groq_api_key or "your_groq_key_here" in settings.groq_api_key:
        logger.error("Groq AI is not configured (missing API key). Skipping.")
        return None
    
    try:
        async with AsyncGroq(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url
        ) as client:
            # Формируем параметры запроса согласно примеру
            params = {
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7, # Температура для контроля случайности (1 это максимальная случайность, 0.5 - средняя, по умолчанию 0.7)
                "top_p": 1,
                "stream": True,
            }

            # Добавляем параметры размышления только если модель их поддерживает
            if "gpt-oss" in settings.groq_model or "o1" in settings.groq_model:
                params["reasoning_effort"] = settings.groq_reasoning_effort
                params["max_completion_tokens"] = 8192
            else:
                params["max_tokens"] = 4096
                # Убираем stream: True если он вызывает проблемы с прокси/сетью (опционально)
                # params["stream"] = False 

            completion = await client.chat.completions.create(**params)
            
            full_response = []
            async for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response.append(chunk.choices[0].delta.content)
            
            return "".join(full_response)
        
    except Exception as e:
        logger.error(f"Error during Groq AI text generation: {str(e)}")
        return None
