"""
Обработчик контента по ключевым словам
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from database.db import get_db_session
from database.models import Content, User
from utils.messages import send_content
from utils.validators import is_admin

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text)
async def handle_keyword(message: Message):
    """Обработка ключевых слов"""
    logger.info(f"🔍 Проверка ключевого слова: '{message.text}' от {message.from_user.id}")
    
    if not message.text:
        return
    
    keyword = message.text.strip().lower()
    
    db = get_db_session()
    try:
        # Проверяем, зарегистрирован ли пользователь (админы могут без регистрации)
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        if not is_admin(message.from_user.id):
            if not user or not user.is_registered:
                logger.info(f"   Пользователь не зарегистрирован, пропускаем")
                return  # Игнорируем незарегистрированных пользователей
        
        # Ищем контент по ключевому слову
        content = db.query(Content).filter(
            Content.keyword == keyword,
            Content.is_active == True
        ).first()
        
        if not content:
            logger.info(f"   Контент не найден для '{keyword}'")
            return  # Ключевое слово не найдено
        
        logger.info(f"📤 Отправка контента по ключевому слову '{keyword}' пользователю {message.from_user.id}")
        # Отправляем контент
        await send_content(message, content)
            
    finally:
        db.close()

