"""
Работа с базой данных
"""
import os
import logging
import time
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import OperationalError, DatabaseError
from database.models import Base
from config import settings

logger = logging.getLogger(__name__)

# Защита от перегрузки БД
_MAX_DB_RETRIES = 3
_DB_RETRY_DELAY = 0.5


# Создаем директорию для БД если её нет
os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)

# Создаем движок БД с настройками для защиты от перегрузки
engine = create_engine(
    f'sqlite:///{settings.DB_PATH}',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
    echo=False,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,   # Переиспользование соединений каждый час
)

# Обработчик для логирования медленных запросов
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Логирование медленных запросов к БД"""
    conn.info.setdefault('query_start_time', []).append(time.time())


@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Логирование медленных запросов к БД"""
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 1.0:  # Запросы дольше 1 секунды
        logger.warning(f"⚠️ Медленный запрос к БД ({total:.2f}s): {statement[:100]}")

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Инициализация базы данных"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"📂 Путь к БД: {settings.DB_PATH}")
    Base.metadata.create_all(bind=engine)
    logger.info(f"✅ База данных инициализирована: {settings.DB_PATH}")


def get_db() -> Session:
    """Получить сессию БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Получить сессию БД (для прямого использования)
    С защитой от ошибок подключения
    """
    retries = 0
    while retries < _MAX_DB_RETRIES:
        try:
            return SessionLocal()
        except (OperationalError, DatabaseError) as e:
            retries += 1
            if retries >= _MAX_DB_RETRIES:
                logger.error(f"❌ Не удалось подключиться к БД после {_MAX_DB_RETRIES} попыток: {e}")
                raise
            logger.warning(f"⚠️ Ошибка подключения к БД (попытка {retries}/{_MAX_DB_RETRIES}): {e}")
            time.sleep(_DB_RETRY_DELAY * retries)  # Экспоненциальная задержка

