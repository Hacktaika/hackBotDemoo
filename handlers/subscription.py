"""
Обработчик проверки подписки
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.db import get_db_session
from database.models import User
from utils.validators import check_channel_subscription
from utils.subscription import show_subscription_request
from handlers.menu import show_main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "check_subscription")
async def check_subscription_handler(callback: CallbackQuery):
    """Проверка подписки"""
    user_id = callback.from_user.id
    logger.info(f"🔍 Проверка подписки пользователя {user_id}")
    
    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            logger.warning(f"⚠️ Пользователь {user_id} не найден в БД")
            await callback.answer("❌ Пользователь не найден. Используй /start", show_alert=True)
            return
        
        bot = callback.bot
        is_subscribed = await check_channel_subscription(bot, user_id)
        
        if is_subscribed:
            logger.info(f"✅ Пользователь {user_id} подписан на оба канала")
            user.is_subscribed = True
            db.commit()
            # Показываем уведомление через callback.answer
            await callback.answer("✅ Отлично! Ты подписан на оба канала!")
            # Редактируем сообщение и показываем меню
            await show_main_menu(callback.message, db, user, edit=True)
        else:
            logger.info(f"⚠️ Пользователь {user_id} не подписан на каналы")
            # Показываем уведомление через callback.answer (всплывающее уведомление)
            await callback.answer("❌ Ты еще не подписан на один или оба канала", show_alert=False)
            # Редактируем существующее сообщение с кнопками (не создаем новое)
            await show_subscription_request(callback.message, bot, edit=True)
    finally:
        db.close()

