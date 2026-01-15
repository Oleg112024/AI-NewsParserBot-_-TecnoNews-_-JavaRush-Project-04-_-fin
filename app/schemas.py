# Pydantic-схемы
from pydantic import BaseModel, Field, AnyHttpUrl
from datetime import datetime


class NewsItem(BaseModel):
    id: str = Field(
        ...,
        description="uuid новости",
        examples=["asd5aag8as5dg348dfas4"]
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Заголовок новости",
        examples=["Вышла новая версия Python 3.15", "Знакомьтесь с новым фреймворком"]
    )
    url: AnyHttpUrl = Field(
        ...,
        description="Оригинальный url новсти",
        examples=["https://habr.com/ru/articles/12345"]
    )
    summary: str | None = Field(
        default=None,
        description="Короткое описание новсти",
        examples=["Краткий обзор новых функций и изменений Python 3.15"]
    )
    source: str  = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Имя источника",
        examples=["РБК"]
    )
    published_at: datetime  = Field(
        ...,
        description="Время публикации на источнике новости",
        examples=["2025-01-01T00:00:00Z"]
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Список ключевых слов",
        examples=[["Python", "FastAPI"]]
    )


class PublishedNews(BaseModel):
    news_id: str = Field(
        ...,
        description="uuid новости",
        examples=["asd5aag8as5dg348dfas4"]
    )
    published_at: datetime  = Field(
        ...,
        description="Время публикации в телеграм канале новости",
        examples=["2025-01-01T00:00:00Z"]
    )
    channel_id: str = Field(
        ...,
        description="id телеграм канала",
        examples=["@my_telegram_chanel", "-10001234355466"]
    )


class Keywords(BaseModel):
    id: int = Field(
        ...,
        description="id ключевого слова",
        examples=[1, 2]
    )
    word: str  = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Ключевое слово новости",
        examples=["python", "fastapi"]
    )


class Source(BaseModel):
    id: str = Field(
        ...,
        description="Уникальный идентификатор источника",
        examples=["habr", "vc_main", "tg_python_news"]
    )
    type: str = Field(
        ...,
        description="Тип источника: сайт или tg",
        examples=["site", "tg"]
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Человекочитаемое имя источника",
        examples=["Habr новости", "VC главная", "Python новости в Telegram"]
    )
    url: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="URL сайта или username/ссылка Telegram-канала",
        examples=["https://habr.com/ru/news/", "@python_news"]
    )
    enabled: bool = Field(
        default=True,
        description="Включён ли источник для парсинга"
    )


class Post(BaseModel):
    id: str = Field(
        ...,
        description="Уникальный идентификатор поста",
        examples=["b1f5b3e8-3e72-4c7a-9f6a-1a2b3c4d5e6f"]
    )
    news_id: str = Field(
        ...,
        description="Идентификатор связанной новости",
        examples=["asd5aag8as5dg348dfas4"]
    )
    generated_text: str = Field(
        ...,
        min_length=1,
        description="Сгенерированный текст поста для публикации"
    )
    published_at: datetime | None = Field(
        default=None,
        description="Время публикации поста в Telegram, если уже опубликован"
    )
    status: str = Field(
        default="new",
        description="Статус поста: new/generated/published/failed",
        examples=["new", "generated", "published"]
    )
