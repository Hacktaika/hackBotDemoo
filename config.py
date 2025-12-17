"""
Конфигурация бота
"""
import os
import logging
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Настройки приложения"""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    BOT_TOKEN: str = Field(..., description="Токен Telegram бота")
    ADMIN_IDS: str = Field(..., description="ID администраторов через запятую")
    CHANNEL1_ID: str = Field(..., description="ID первого канала")
    CHANNEL2_ID: str = Field(..., description="ID второго канала")
    CHANNEL1_USERNAME: str = Field(..., description="Username первого канала")
    CHANNEL2_USERNAME: str = Field(..., description="Username второго канала")
    SITE_URL: str = Field(default="https://example.com", description="URL сайта")
    DB_PATH: str = Field(default="./data/bot.db", description="Путь к БД")
    
    @field_validator('ADMIN_IDS')
    @classmethod
    def validate_admin_ids(cls, v) -> str:
        """Валидация ID администраторов (оставляем как строку)"""
        if isinstance(v, str):
            # Проверяем, что можно распарсить
            try:
                ids = [int(admin_id.strip()) for admin_id in v.split(',') if admin_id.strip()]
                if not ids:
                    raise ValueError("ADMIN_IDS не может быть пустым")
                return v  # Возвращаем строку как есть
            except ValueError as e:
                raise ValueError(f"ADMIN_IDS должен содержать числа, разделенные запятыми: {e}")
        raise ValueError("ADMIN_IDS должен быть строкой")
    
    @property
    def admin_ids_list(self) -> List[int]:
        """Список ID администраторов"""
        try:
            return [int(admin_id.strip()) for admin_id in self.ADMIN_IDS.split(',') if admin_id.strip()]
        except (ValueError, AttributeError) as e:
            logger.error(f"Ошибка парсинга ADMIN_IDS: {e}")
            return []


def load_settings() -> Settings:
    """Загрузка настроек с обработкой ошибок"""
    try:
        if not os.path.exists('.env'):
            logger.error("❌ Файл .env не найден!")
            logger.error("📝 Создайте файл .env на основе .env.example и заполните все необходимые переменные")
            raise FileNotFoundError(
                "Файл .env не найден. Создайте его на основе .env.example"
            )
        
        logger.info("📋 Загрузка конфигурации из .env...")
        settings = Settings()
        logger.info("✅ Конфигурация успешно загружена")
        logger.info(f"   • Бот токен: {settings.BOT_TOKEN[:10]}...")
        try:
            admin_count = len(settings.admin_ids_list)
            logger.info(f"   • Админов: {admin_count}")
        except Exception:
            logger.warning("   • Админов: не удалось определить")
        logger.info(f"   • Каналы: {settings.CHANNEL1_USERNAME}, {settings.CHANNEL2_USERNAME}")
        return settings
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
        logger.error("💡 Убедитесь, что файл .env существует и содержит все необходимые переменные")
        raise


# Глобальный экземпляр настроек
settings = load_settings()

# Удобный доступ к списку админов
ADMIN_IDS = settings.admin_ids_list

# ===============================
# КРУЖОЧКИ ДЛЯ ВОПРОСОВ РЕГИСТРАЦИИ
# ===============================
# Отправь кружочек боту (как админ), чтобы получить file_id
# Затем вставь file_id сюда

# Вопрос 1: "Как тебя зовут?"
VIDEO_NOTE_NAME = "DQACAgIAAxkBAAMpaULIgzMAAe9PAS74iPaVTZwOtm6wAAI7kgACrRz4SQgLQTwPoHOxNgQ"

# Вопрос 2: "Чем занимаешься? Какая должность?"
VIDEO_NOTE_POSITION = "DQACAgIAAxkBAAMxaULVzuFcsZqg3kdmWvogptLapqMAAj2SAAKtHPhJ3PPLqcFazHQ2BA"

# Вопрос 3: "Что хочешь получить от бота?"
VIDEO_NOTE_EXPECTATIONS = "DQACAgIAAxkBAAMzaULV5XLgVvrhj37nivtoG73Z8YwAAj-SAAKtHPhJex2vmCavRKE2BA"

# Вопрос 4: "Как узнал о боте?"
VIDEO_NOTE_SOURCE = "DQACAgIAAxkBAAM1aULV9jRl3m7R6-551-34q3uOx-MAAkCSAAKtHPhJnotY15vd5YY2BA"

# После завершения регистрации (перед меню/подпиской)
VIDEO_NOTE_FINISH = "DQACAgIAAxkBAAM3aULWBUhUaODfSrgSyi34I0UP-E8AAkGSAAKtHPhJn36PVbkkPNQ2BA"

