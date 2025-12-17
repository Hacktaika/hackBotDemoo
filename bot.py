"""
Главный файл запуска бота
"""
import asyncio
import logging

# Настройка логирования ПЕРЕД импортом config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from database.db import init_db
from handlers.start import router as start_router
from handlers.registration import router as registration_router
from handlers.subscription import router as subscription_router
from handlers.menu import router as menu_router
from handlers.info import router as info_router
from handlers.quiz import router as quiz_router
from handlers.content import router as content_router
from handlers.admin import router as admin_router


async def main():
    """Главная функция"""
    logger.info("=" * 50)
    logger.info("🚀 Запуск Hacktaika Bot")
    logger.info("=" * 50)
    
    try:
        # Инициализация БД
        logger.info("📦 Инициализация базы данных...")
        init_db()
        logger.info("✅ База данных готова")
        
        # Создание бота и диспетчера
        logger.info("🤖 Создание бота...")
        bot = Bot(token=settings.BOT_TOKEN)
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот авторизован: @{bot_info.username} (ID: {bot_info.id})")
        
        dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрация роутеров
        logger.info("📋 Регистрация обработчиков...")
        dp.include_router(admin_router)  # Админка первой!
        dp.include_router(start_router)
        dp.include_router(registration_router)
        dp.include_router(subscription_router)
        dp.include_router(menu_router)
        dp.include_router(info_router)
        dp.include_router(quiz_router)
        dp.include_router(content_router)  # Контент последним — ловит все текстовые сообщения
        logger.info("✅ Обработчики зарегистрированы")
        
        logger.info("=" * 50)
        logger.info("✅ Бот запущен и готов к работе!")
        logger.info("=" * 50)
        
        # Запуск polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️  Бот остановлен")

