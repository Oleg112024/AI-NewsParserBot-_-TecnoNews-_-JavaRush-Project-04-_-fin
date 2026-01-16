from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    debug: bool = Field(default=False, validation_alias="DEBUG")
    redis_url: str = Field(..., validation_alias="REDIS_URL")
    app_version: str = Field(default="v.0.3.35AI-MENU", validation_alias="APP_VERSION")

    # Telegram API Credentials
    telegram_api_id: int = Field(default=0, validation_alias="TELEGRAM_API_ID")
    telegram_api_hash: str = Field(default="", validation_alias="TELEGRAM_API_HASH")
    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_channel_id: str = Field(default="", validation_alias="TELEGRAM_CHANNEL_ID")

    # News Settings
    news_keywords: str = Field(default="", validation_alias="NEWS_KEYWORDS")
    news_time: int = Field(default=30, validation_alias="NEWS_TIME")
    max_news_items: int = Field(default=100, validation_alias="MAX_NEWS_ITEMS")
    news_time_call: int = Field(default=30, validation_alias="NEWS_TIME_CALL")
    time_life_news: int = Field(default=172800, validation_alias="TIME_LIFE_NEWS")
    timezone: str = Field(default="UTC", validation_alias="TIMEZONE")
    utc_offset: int = Field(default=0, validation_alias="UTC_OFFSET")

    # Logging Settings
    log_max_bytes: int = Field(default=10485760, validation_alias="LOG_MAX_BYTES")
    log_rotation_count: int = Field(default=3, validation_alias="LOG_ROTATION_COUNT")
    error_log_rotation_count: int = Field(default=5, validation_alias="ERROR_LOG_ROTATION_COUNT")

    # AI Agent Settings (Multi-provider)
    ai_agent: str = Field(default="off", validation_alias="AI_AGENT")  # "on" или "off"
    ai_provider: str = Field(default="groq", validation_alias="AI_PROVIDER")  # "groq" или "openai"
    
    # Groq Settings
    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", validation_alias="GROQ_MODEL")
    groq_base_url: str = Field(default="https://api.groq.com", validation_alias="GROQ_BASE_URL")
    groq_reasoning_effort: str = Field(default="medium", validation_alias="GROQ_REASONING_EFFORT")

    # OpenAI Settings
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", validation_alias="OPENAI_MODEL")
    openai_base_url: str = Field(default="https://api.openai.com/v1", validation_alias="OPENAI_BASE_URL")

    # DeepSeek Settings
    deepseek_api_key: str = Field(default="", validation_alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-chat", validation_alias="DEEPSEEK_MODEL")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", validation_alias="DEEPSEEK_BASE_URL")

    @property
    def keywords_list(self) -> list[str]:
        raw_value = self.news_keywords
        parts = [part.strip() for part in raw_value.split(',') if part.strip()]
        return parts


settings = Settings()
