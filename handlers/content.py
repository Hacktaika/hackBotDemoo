"""
Обработчик контента по ключевым словам
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from database.db import get_db_session
from database.models import Content, User
from utils.messages import send_content

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text)
async def handle_keyword(message: Message):
    """Обработка ключевых слов"""
    if not message.text:
        return
    
    keyword = message.text.strip().lower()
    
    db = get_db_session()
    try:
        # Проверяем, зарегистрирован ли пользователь
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        if not user or not user.is_registered:
            return  # Игнорируем незарегистрированных пользователей
        
        # Ищем контент по ключевому слову
        content = db.query(Content).filter(
            Content.keyword == keyword,
            Content.is_active == True
        ).first()
        
        if not content:
            return  # Ключевое слово не найдено
        
        logger.info(f"📤 Отправка контента по ключевому слову '{keyword}' пользователю {message.from_user.id}")
        # Отправляем контент
        await send_content(message, content)
            
    finally:
        db.close()

