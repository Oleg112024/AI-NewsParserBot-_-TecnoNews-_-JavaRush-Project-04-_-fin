import logging
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

async def generate_text_deepseek(prompt: str, system_message: str = "You are a helpful assistant.") -> str | None:
    """
    Генерация текста с использованием DeepSeek API.
    """
    if not settings.deepseek_api_key:
        logger.error("DeepSeek API key is not configured. Skipping.")
        return None

    try:
        async with AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url
        ) as client:
            response = await client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            result = response.choices[0].message.content
            if result:
                logger.info(f"Successfully generated text with DeepSeek ({len(result)} chars)")
            return result

    except Exception as e:
        logger.error(f"Error during DeepSeek AI text generation: {str(e)}")
        return None
