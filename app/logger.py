import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from app.config import settings

def setup_logging(service_name: str):
    """
    Настраивает логирование: вывод в консоль и в файл.
    Файлы логов сохраняются в папку /app/logs внутри контейнера.
    В имени файла указывается дата и время создания.
    """
    log_dir = "/app/logs"
    
    # Сначала создаем базовый логгер, чтобы видеть ошибки инициализации в консоли
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Проверка доступности директории
    if not os.path.exists(log_dir):
        try:
            # создание папки logs в корне проекта, если она не существует
            os.makedirs(log_dir, exist_ok=True)
            root_logger.info(f"Created log directory: {log_dir}")
        except Exception as e:
            # создание папки logs в корне контейнера, если папка в корне проекта недоступна
            root_logger.warning(f"Could not create {log_dir}: {e}. Falling back to 'logs' directory.")
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)

    # Проверка прав на запись
    if not os.access(log_dir, os.W_OK):
        root_logger.warning(f"Directory {log_dir} is NOT writable! Trying 'logs' in current directory.")
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.abspath(os.path.join(log_dir, f"{service_name}_{timestamp}.log"))
    error_log_file = os.path.abspath(os.path.join(log_dir, f"errors_{service_name}.log"))
    
    try:
        # Основной обработчик для всех логов (INFO и выше)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=settings.log_max_bytes, 
            backupCount=settings.log_rotation_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        
        # Специальный обработчик только для ошибок (ERROR и выше)
        # Этот файл не имеет таймстампа в имени, чтобы он был постоянным и его было легче мониторить
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.error_log_rotation_count, # Используем настройку из .env
            encoding='utf-8'
        )
        error_handler.setFormatter(log_formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)

        root_logger.info(f"Logging to file of the container: {log_file}")
        root_logger.info(f"Critical errors will be mirrored to of the container: {error_log_file}")
    except Exception as e:
        root_logger.error(f"FAILED to initialize file logging: {e}")
    
    # Подавляем лишние логи от сторонних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return logging.getLogger(service_name)
