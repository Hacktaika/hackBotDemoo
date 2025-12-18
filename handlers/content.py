"""
Обработчик контента по ключевым словам
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from database.db import get_db_session
from database.models import Content, User
from utils.messages import send_content
from utils.validators import is_admin, validate_message_size
from utils.rate_limit import check_content_keyword_rate_limit

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text)
async def handle_keyword(message: Message):
    """Обработка ключевых слов"""
    user_id = message.from_user.id
    logger.info(f"🔍 Проверка ключевого слова: '{message.text}' от {user_id}")
    
    if not message.text:
        return
    
    # Валидация размера сообщения
    if not validate_message_size(message):
        logger.warning(f"🚫 Пользователь {user_id} отправил слишком большое сообщение")
        return
    
    # Проверка rate limit для поиска по ключевым словам
    if not is_admin(user_id):
        allowed, error_msg = check_content_keyword_rate_limit(user_id)
        if not allowed:
            logger.warning(f"🚫 Пользователь {user_id} превысил лимит поиска по ключевым словам")
            try:
                await message.answer(error_msg)
            except:
                pass
            return
    
    # Ограничение длины ключевого слова
    if len(message.text) > 100:
        logger.warning(f"🚫 Пользователь {user_id} отправил слишком длинное ключевое слово")
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

