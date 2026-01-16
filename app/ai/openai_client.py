import logging
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

async def generate_text_openai(prompt: str, system_message: str = "You are a helpful assistant.") -> str | None:
    """
    Генерирует текст с помощью OpenAI.
    """
    if not settings.openai_api_key or "ваш_ключ" in settings.openai_api_key:
        logger.error("OpenAI is not configured (missing API key). Skipping.")
        return None
    
    try:
        async with AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        ) as client:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            result = response.choices[0].message.content
            if result:
                logger.info(f"Successfully generated text with OpenAI ({len(result)} chars)")
            return result

    except Exception as e:
        if "insufficient_quota" in str(e):
            logger.error("OpenAI Error: Insufficient quota. Please check your billing/balance.")
        else:
            logger.error(f"Error during OpenAI text generation: {str(e)}")
        return None
