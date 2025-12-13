"""
Работа с базой данных
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from database.models import Base
from config import settings


# Создаем директорию для БД если её нет
os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)

# Создаем движок БД
engine = create_engine(
    f'sqlite:///{settings.DB_PATH}',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
    echo=False
)

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
    """Получить сессию БД (для прямого использования)"""
    return SessionLocal()

