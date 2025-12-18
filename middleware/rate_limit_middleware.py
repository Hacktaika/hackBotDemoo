"""
Middleware для защиты от спама и DDoS
"""
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from utils.rate_limit import (
    check_message_rate_limit,
    check_callback_rate_limit,
    check_admin_rate_limit
)
from utils.validators import is_admin

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """Middleware для rate limiting"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка события с проверкой rate limit"""
        
        # Для сообщений
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            
            if user_id:
                # Админы имеют более мягкие ограничения
                if is_admin(user_id):
                    # Для админов проверяем только очень агрессивный спам
                    allowed, message = check_message_rate_limit(user_id)
                    if not allowed:
                        logger.warning(f"🚫 Админ {user_id} превысил лимит сообщений")
                        try:
                            await event.answer("⛔ Слишком много запросов. Подождите немного.")
                        except:
                            pass
                        return
                else:
                    # Для обычных пользователей строгие ограничения
                    allowed, message = check_message_rate_limit(user_id)
                    if not allowed:
                        logger.warning(f"🚫 Пользователь {user_id} превысил лимит сообщений: {message}")
                        try:
                            await event.answer(message)
                        except:
                            pass
                        return
        
        # Для callback queries
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            
            if user_id:
                # Админы имеют более мягкие ограничения
                if is_admin(user_id):
                    allowed, message = check_callback_rate_limit(user_id)
                    if not allowed:
                        logger.warning(f"🚫 Админ {user_id} превысил лимит callback'ов")
                        try:
                            await event.answer("⛔ Слишком много запросов. Подождите немного.", show_alert=True)
                        except:
                            pass
                        return
                else:
                    allowed, message = check_callback_rate_limit(user_id)
                    if not allowed:
                        logger.warning(f"🚫 Пользователь {user_id} превысил лимит callback'ов: {message}")
                        try:
                            await event.answer(message, show_alert=True)
                        except:
                            pass
                        return
        
        # Продолжаем обработку
        return await handler(event, data)

