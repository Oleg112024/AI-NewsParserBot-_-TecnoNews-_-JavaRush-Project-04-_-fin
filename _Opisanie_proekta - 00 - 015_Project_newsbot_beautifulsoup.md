# проанализируй ещё техническое задание "_M4 Project FastAPI - telegram - ТЗ Проекта FastAPI + Телеграм" и весь проект и разработай план для работы, и будем двигаться для заведшения проекта


### Сейчас сделаю именно то, что ты просишь:

1. опишу, что требует ТЗ,
2. что уже есть в проекте,
3. дам поэтапный план до завершения проекта с учётом текущего кода.
1. Кратко про требования ТЗ

Из файла _M4 Project FastAPI - telegram - ТЗ Проекта FastAPI + Телеграм.md:15-40 нужно:

- Собирать новости:
  - с сайтов: https://habr.com/ru/articles/ , https://vc.ru/ , https://tproger.ru/ , https://3dnews.ru/ , https://ixbt.com/
  - из публичных Telegram-каналов (Telethon).
- Каждая новость: title , url? , summary , source , published_at , raw_text? .
- Обрабатывать всё через очередь задач:
  - Celery + Redis, цепочка: парсинг → фильтрация → AI-генерация → публикация.
- AI‑генерация:
  - OpenAI GPT‑4 или аналог, промпт «кратко, интересно, emoji + call to action».
  - Обработка ошибок, ручное тестирование через API.
- Фильтрация:
  - по ключевым словам/языку/источнику, исключение дублей.
- Публикация:
  - в Telegram через Telethon, защита от дублей, логирование ошибок и успешных постов.
- Панель управления (через API):
  - CRUD для источников ( Source ), ключевых слов ( Keyword ).
  - История постов ( Post ), логи ошибок.
- Документация:
  - Авто /docs , эндпоинты: новости, генерация, публикация, источники, фильтры.
2. Текущее состояние проекта

По коду в репозитории:

- FastAPI-приложение
  - main.py:1-29 — точка входа:
    - создаётся app = FastAPI(...) ;
    - корневой маршрут / возвращает "Hello World!" и settings.debug ;
    - подключён api_router из app.api .
  - app/api.py:1-36 :
    - GET /health — статус сервиса;
    - GET /news — возвращает фиктивный список NewsItem (моковые данные).
- Схемы данных
  - app/schemas.py:1-79 :
    - NewsItem — pydantic-модель новости (id, title, url, summary, source, published_at, keywords).
    - PublishedNews — факт публикации в Telegram (news_id, published_at, channel_id).
    - Keywords — id + слово.
  - Это близко к ТЗ, но нет Post , Source в виде схем.
- Конфигурация
  - app/config.py:1-28 :
    - Settings с:
      - debug ;
      - redis_url = 'redis://localhost:6379/0' ;
      - параметры Telegram ( telegram_api_id , telegram_api_hash , telegram_bot_token , telegram_channel_id );
      - news_keywords и удобное свойство keywords_list .
    - Это уже готовая точка для фильтрации и интеграции с Redis/Telegram.
- Структура под архитектуру из ТЗ уже заложена
  - app/news_parser/ :
    - habr.py:1-4 — только константы, причём с синтаксической ошибкой ( HABR_NEWS_URL f"... без = ).
    - rbc.py:1 — один комментарий.
    - main.py — пустой.
  - app/telegram/ :
    - bot.py:1 — комментарий “Наш клиент Telegram”.
    - publisher.py:1 — комментарий “Модуль для отправки сообщений”.
  - app/tasks.py:1 — комментарий “Задачи Celery”.
  - app/utils.py:1 — комментарий “Вспомогательные утилиты”.
  - app/__init__.py — пустой.
- Зависимости
  - pyproject.toml:1-23 :
    - Стек: fastapi , uvicorn[stadard] , python-dotenv , pydantic , pydantic-settings , requests , beautifulsoup4 .
    - Опечатка: uvicorn[stadard] → должно быть uvicorn[standard] .
    - Нет celery , redis , telethon , openai или аналогов.
  - requirements.txt:1-14 — базовый стек FastAPI, без Celery/Redis/Telethon/AI.
- Архитектурные описания
  - newsbot_architecture.md:1-37 — уже описывает задумку:
    - app/news_parser → app/tasks → Redis → Telegram.
  - _M4 Project FastAPI - telegram - ТЗ ...md — полное ТЗ и roadmap.
Итого: Архитектура и каркас FastAPI есть, схемы частично есть, структуры каталогов под парсер/Telegram/Celery есть, но вся «мясистая» логика (парсинг, Celery, фильтрация, AI, публикация, CRUD-API, логирование) пока не реализована.

3. Рабочий план до завершения проекта

Я буду исходить из того, что:

- Хранилище делаем максимально простым, но совместимым с многопроцессной обработкой:
  - используем Redis не только как брокер, но и как хранилище новостей и постов (ключи/JSON). Это укладывается в ТЗ (Redis уже нужен).
- БД типа Postgres/SQLite не вводим без необходимости — это учебный проект.
Разобью план на этапы, которыми можно идти последовательно.

Этап 1. Приведение окружения и каркаса в порядок

Цель: проект стабильно устанавливается и запускается.

- Исправить синтаксические/конфигурационные мелочи:
  - app/news_parser/habr.py:1-4 — добавить = к константам.
  - pyproject.toml:9-16 — исправить uvicorn[stadard] → uvicorn[standard] .
- Синхронизировать зависимости:
  - Добавить в pyproject.toml и (при необходимости) в requirements.txt :
    - celery ,
    - redis ,
    - telethon ,
    - openai (или совместимый клиент, который выберем),
    - при необходимости python-dotenv , beautifulsoup4 уже есть.
- Уточнить структуру модулей под ТЗ:
  - Убедиться, что есть каталоги: app/news_parser , app/telegram , app/ai , app/ ( tasks.py , utils.py , будущий models.py ).
Результат этапа: Сервер FastAPI запускается, зависимости ставятся без ошибок, структура проекта соответствует архитектуре из ТЗ.

Этап 2. Модели данных и хранилище (через Redis)

Цель: определён единый формат данных и место, где всё хранится.

- Добавить недостающие модели в app/schemas.py :
  - Source (id, type=site/tg, name, url/username, enabled);
  - Post (id, news_id, generated_text, published_at?, status).
- Определить внутренние ключи в Redis:
  - news:{id} — объект новости;
  - список/множество news_ids или news:status:new и т.д.;
  - posts:{id} — объект поста;
  - sources , keywords .
- В app/utils.py реализовать простые функции-обёртки:
  - сохранение/получение новостей, постов, источников, ключевых слов в Redis;
  - генерация id (uuid4) и хэшей для дедупликации.
Результат: Есть понятное хранилище новостей и постов, API и Celery‑таски будут работать с ним.

Этап 3. Парсинг новостей с сайтов

Цель: реально получать новости хотя бы с 1–2 сайтов (минимум — Habr + ещё один, напр. VC или РБК).

- app/news_parser/habr.py :
  - Реализовать функции:
    - fetch_habr_news() -> list[NewsItem] :
      - запрос к https://habr.com/ru/articles/ ,
      - парсинг HTML через BeautifulSoup ,
      - выделение title, url, summary/краткое описание, published_at, source="Habr".
    - при необходимости — отдельная функция для загрузки полной статьи.
- Аналогично для app/news_parser/rbc.py (или одного из других сайтов из ТЗ).
- В app/news_parser/main.py :
  - Общая функция fetch_all_site_news(sources: list[Source]) -> list[NewsItem] , которая вызывает конкретные парсеры по type/url.
- При сохранении:
  - Сразу генерировать id, проверять дубли по хэшу ( title+source или url ) и складывать новости в Redis.
Результат: Запустив функцию парсинга, можно получить список свежих NewsItem от сайтов и увидеть их через временный тестовый endpoint (например, /news вместо моков позже).

Этап 4. Парсер Telegram-каналов (чтение)

Цель: научиться читать посты из публичных каналов по списку источников type= tg .

- app/telegram/bot.py :
  - Инициализировать Telethon‑клиент с данными из settings.telegram_api_id , settings.telegram_api_hash .
- app/news_parser/telegram.py :
  - Функция fetch_telegram_news(source: Source) -> list[NewsItem] :
    - читает последние N сообщений из канала source.url /username;
    - формирует NewsItem с raw_text и возможным url .
- Интеграция в app/news_parser/main.py :
  - Добавить обработку источников type= tg аналогично сайтам.
Результат: Есть единый интерфейс fetch_all_news() (сайты + tg) с данными в Redis.

Этап 5. Celery + Redis: очередь задач и пайплайн

Цель: сделать фоновые задачи и цепочку из ТЗ.

- В app/tasks.py :
  - Настроить Celery-приложение:
    - celery = Celery(__name__, broker=settings.redis_url, backend=settings.redis_url) .
  - Определить задачи:
    - fetch_news_task — вызывает fetch_all_news , складывает новости в Redis, возвращает список id или их количество.
    - filter_news_task — берёт новые новости, фильтрует по ключевым словам/источникам, убирает дубли (используя utils + settings.keywords_list ).
    - generate_post_task — для каждого отфильтрованного id вызывает AI‑генерацию (Этап 6), создаёт записи Post со status="generated" .
    - publish_post_task — публикует в Telegram (Этап 7) и обновляет status="published" и published_at .
  - Собрать цепочку:
    - news_pipeline = chain(fetch_news_task.s(), filter_news_task.s(), generate_post_task.s(), publish_post_task.s()) .
- Настроить Celery Beat (можно через celery.conf.beat_schedule или отдельный конфиг):
  - Периодический запуск fetch_news_task или целой цепочки каждые 30 минут.
Результат: Можно запустить воркер Celery и получить автоматическую обработку новостей в фоне.

Этап 6. AI‑генерация постов

Цель: превратить новости в «красивые» телеграм‑посты.

- Создать пакет app/ai/ :
  - openai_client.py — обёртка над SDK:
    - читает OPENAI_API_KEY из .env через Settings ;
    - даёт функцию generate(text: str, prompt: str) -> str с обработкой ошибок (rate limit, network, unexpected).
  - generator.py :
    - функция generate_post(news: NewsItem) -> str :
      - формирует базовый промпт из ТЗ: кратко, интересно, emoji, call to action, русский язык;
      - вызывает клиент и возвращает текст поста.
- Интегрировать в generate_post_task (Этап 5):
  - принимаем список id новостей, для каждой создаём Post с generated_text и status="generated" .
Результат: Для новых новостей в Redis появляются сгенерированные посты.

Этап 7. Публикация в Telegram через Telethon

Цель: отправка постов в канал и логирование.

- app/telegram/publisher.py :
  - функция publish_to_channel(text: str, channel_id: str) -> str :
    - использует Telethon‑клиент из bot.py ,
    - отправляет сообщение в settings.telegram_channel_id или указанный канал,
    - возвращает message_id или ссылку.
- Интеграция в publish_post_task :
  - для каждого Post со статусом "generated" :
    - отправляем в канал;
    - обновляем статус, published_at , сохраняем лог (минимум в логгер + поле в Redis).
  - Защита от повторной публикации:
    - проверка поля status , опционально — отдельный set с опубликованными news_id.
Результат: Сгенерированные посты реально появляются в Telegram‑канале, ошибки пишутся в логи.

Этап 8. REST API для управления и мониторинга

Цель: реализовать панель управления из ТЗ.

- Расширить/переструктурировать app/api.py (или создать подмодуль app/api/endpoints.py ):
  - /api/sources/ — CRUD по Source :
    - GET список, POST добавить, PUT/PATCH редактировать, DELETE отключить/удалить.
  - /api/keywords/ — CRUD по Keyword :
    - хранение в Redis + синхронизация с settings.news_keywords (или хранить только в Redis, а Settings использовать как дефолт).
  - /api/posts/ — история постов:
    - GET список, фильтры по статусу, дате, источнику.
  - /api/generate/ — ручная генерация:
    - POST с news_id или текстом,
    - возвращает сгенерированный пост, опционально публикует, если передан флаг.
- Обновить /news :
  - вместо моков получать реальные новости из Redis.
Результат: Через /docs видно все нужные эндпоинты, можно управлять источниками/ключевыми словами/постами и запускать ручную генерацию.

Этап 9. Логирование, документация и финальная полировка

Цель: довести до состояния сдачи по чек‑листу ТЗ.

- Логирование:
  - В app/config.py или отдельном модуле настроить logging :
    - уровень, формат, логирование Celery‑тасок, ошибок AI и Telegram, успешных публикаций.
- Документация API:
  - Убедиться, что описания в схемах ( Field.description , examples ) и docstring‑и у эндпоинтов достаточно подробные, чтобы /docs выглядело понятно.
- README/чек‑лист:
  - По ТЗ нужен README.md и чек‑лист, но, по текущим ограничениям, мы не будем создавать новые .md файлы, пока ты явно не попросишь.
  - Планом можно заложить: как только скажешь, добавим README с инструкциями по запуску (FastAPI, Redis, Celery, Telethon, AI).
Что я предлагаю делать дальше

Следующий логичный шаг в реализации — Этап 1 + начало Этапа 2 :

1. Подправить синтаксис и зависимости ( habr.py , pyproject.toml + добавить Celery/Redis/Telethon/OpenAI).
2. Добавить схемы Source и Post и минимальные обёртки для работы с Redis.
Когда скажешь «поехали», я начну прямо в этом репозитории вносить эти изменения по плану, с привязкой к файлам и с проверкой запуска FastAPI.

