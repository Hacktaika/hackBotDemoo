"""
Webhook-версия бота для деплоя на Vercel или любой другой хостинг с вебхуками.

Важно:
- `bot.py` оставлен как есть (long polling, запуск локально: `python bot.py`).
- Этот файл содержит общую инициализацию `Bot` и `Dispatcher` и функцию
  `process_update`, которую можно вызывать из HTTP-хендлера (например, Vercel).

Типовой сценарий для Vercel:
- создаём файл `api/webhook.py`, который:
  - получает JSON от Telegram (HTTP POST),
  - передаёт dict в `process_update`,
  - возвращает HTTP 200.
"""

import asyncio
import logging
from typing import Dict, Any

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from config import settings
from database.db import init_db
from middleware.rate_limit_middleware import RateLimitMiddleware
from handlers.start import router as start_router
from handlers.registration import router as registration_router
from handlers.subscription import router as subscription_router
from handlers.menu import router as menu_router
from handlers.info import router as info_router
from handlers.quiz import router as quiz_router
from handlers.content import router as content_router
from handlers.demo_projects import router as demo_projects_router
from handlers.pdf import router as pdf_router
from handlers.admin import router as admin_router


# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Глобальные объекты бота и диспетчера для повторного использования в serverless-среде
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


def setup_dispatcher() -> None:
    """
    Регистрация middleware и роутеров.
    Вызывается один раз при импорте модуля.
    """
    logger.info("📦 Инициализация базы данных (webhook)...")
    init_db()
    logger.info("✅ База данных готова (webhook)")

    # Middleware защиты
    logger.info("🛡️ Регистрация middleware защиты (webhook)...")
    rate_limit_middleware = RateLimitMiddleware()
    dp.message.outer_middleware(rate_limit_middleware)
    dp.callback_query.outer_middleware(rate_limit_middleware)
    logger.info("✅ Middleware защиты зарегистрированы (webhook)")

    # Роутеры
    logger.info("📋 Регистрация обработчиков (webhook)...")
    dp.include_router(admin_router)  # Админка первой
    dp.include_router(start_router)
    dp.include_router(registration_router)
    dp.include_router(subscription_router)
    dp.include_router(menu_router)
    dp.include_router(info_router)
    dp.include_router(demo_projects_router)
    dp.include_router(pdf_router)
    dp.include_router(quiz_router)
    dp.include_router(content_router)
    logger.info("✅ Обработчики зарегистрированы (webhook)")


_dispatcher_is_ready = False


async def process_update(update_data: Dict[str, Any]) -> None:
    """
    Обработка одного апдейта Telegram в режиме webhook.

    - `update_data` — dict с JSON, который Telegram присылает в вебхук.
    - Функция НЕ возвращает HTTP-ответ — это делает веб-сервер/платформа (Vercel).
    """
    global _dispatcher_is_ready

    if not _dispatcher_is_ready:
        # Инициализируем диспетчер и БД один раз при первом апдейте
        setup_dispatcher()
        _dispatcher_is_ready = True

    try:
        update = Update.model_validate(update_data)
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга Update: {e}", exc_info=True)
        return

    try:
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"❌ Ошибка обработки апдейта: {e}", exc_info=True)


def process_update_sync(update_data: Dict[str, Any]) -> None:
    """
    Синхронная обёртка, чтобы можно было вызывать из обычной функции (как на Vercel).
    """
    asyncio.run(process_update(update_data))


__all__ = [
    "bot",
    "dp",
    "process_update",
    "process_update_sync",
]


