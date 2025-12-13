"""
Статистика
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.db import get_db_session
from database.models import User
from utils.validators import is_admin

router = Router()


@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    """Показать статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    
    db = get_db_session()
    try:
        total_users = db.query(User).count()
        registered_users = db.query(User).filter(User.is_registered == True).count()
        subscribed_users = db.query(User).filter(User.is_subscribed == True).count()
        
        stats_text = (
            f"📊 Статистика\n\n"
            f"Всего пользователей: {total_users}\n"
            f"Зарегистрировано: {registered_users}\n"
            f"Подписаны на каналы: {subscribed_users}"
        )
        
        await callback.message.answer(stats_text)
    finally:
        db.close()

