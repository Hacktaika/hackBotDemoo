"""
Обработчик подарков
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import not_
from database.db import get_db_session
from database.models import Gift, UserGift, User
from utils.keyboards import create_back_button
from utils.messages import send_gift
from handlers.menu import show_main_menu

router = Router()


@router.callback_query(F.data.startswith("gift_"))
async def show_gift(callback: CallbackQuery):
    """Показать подарок"""
    await callback.answer()
    
    gift_id = int(callback.data.split("_")[1])
    
    db = get_db_session()
    try:
        gift = db.query(Gift).filter(Gift.id == gift_id).first()
        user = db.query(User).filter(User.telegram_id == callback.from_user.id).first()
        
        if not gift or not user:
            await callback.message.answer("❌ Подарок не найден")
            return
        
        # Проверяем, не получил ли уже
        existing = db.query(UserGift).filter(
            UserGift.user_id == user.id,
            UserGift.gift_id == gift.id
        ).first()
        
        if existing:
            await callback.message.answer("✅ Ты уже получил этот подарок!")
            return
        
        # Отправляем подарок
        text = f"🎁 {gift.name}\n\n"
        if gift.description:
            text += f"{gift.description}\n\n"
        if gift.text:
            text += gift.text
        
        keyboard = create_back_button()
        
        await send_gift(callback, gift, text, keyboard)
        
        # Сохраняем, что пользователь получил подарок
        user_gift = UserGift(user_id=user.id, gift_id=gift.id)
        db.add(user_gift)
        user.has_bonus = True
        db.commit()
        
        # Обновляем меню (убираем кнопку подарка) - не редактируем, т.к. это новое сообщение с подарком
        # Меню будет показано при следующем обращении
        
    finally:
        db.close()

