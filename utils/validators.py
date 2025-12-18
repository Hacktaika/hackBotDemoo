"""
Валидация и проверки
"""
import logging
from typing import Optional
from aiogram import Bot
from aiogram.types import ChatMember
from config import settings

logger = logging.getLogger(__name__)


def _normalize_channel_id(channel_id):
    """
    Преобразует ID канала в правильный формат для Telegram API
    
    Args:
        channel_id: ID канала (может быть строкой, числом или username)
        
    Returns:
        Нормализованный ID канала (int для ID или str для username)
    """
    # Если это username (начинается с @), возвращаем как есть
    if isinstance(channel_id, str) and channel_id.startswith('@'):
        return channel_id
    
    # Если это строка с числом, преобразуем в int
    if isinstance(channel_id, str):
        # Убираем пробелы
        channel_id = channel_id.strip()
        # Если это username без @, добавляем @
        if not channel_id.startswith('@') and not channel_id.lstrip('-').isdigit():
            return f"@{channel_id}"
        # Пытаемся преобразовать в число
        try:
            channel_id = int(channel_id)
        except ValueError:
            # Если не число, возможно это username без @
            return f"@{channel_id}" if not channel_id.startswith('@') else channel_id
    
    # Если это положительное число, преобразуем в формат канала -100XXXXXXXXXX
    if isinstance(channel_id, int) and channel_id > 0:
        # Для каналов Telegram использует формат: -100 + ID
        # Но нужно правильно сформировать число
        # Например: 1541113270 -> -1001541113270
        channel_str = str(channel_id)
        return int(f"-100{channel_str}")
    
    # Если уже отрицательное число, возвращаем как есть
    return channel_id


async def check_channel_subscription(bot: Bot, user_id: int) -> bool:
    """
    Проверка подписки пользователя на оба канала
    
    Args:
        bot: Экземпляр бота
        user_id: ID пользователя
        
    Returns:
        True если подписан на оба канала, иначе False
    """
    try:
        # Получаем ID каналов из настроек
        channel1_raw = settings.CHANNEL1_ID
        channel2_raw = settings.CHANNEL2_ID
        
        # Нормализуем ID каналов
        channel1_id = _normalize_channel_id(channel1_raw)
        channel2_id = _normalize_channel_id(channel2_raw)
        
        logger.info(f"🔍 Проверка подписки пользователя {user_id}")
        logger.info(f"   Канал 1: {channel1_raw} -> {channel1_id} (тип: {type(channel1_id).__name__})")
        logger.info(f"   Канал 2: {channel2_raw} -> {channel2_id} (тип: {type(channel2_id).__name__})")
        
        # Проверяем первый канал
        subscribed1 = False
        channel1_checked = False
        
        # Сначала пробуем по ID
        try:
            member1 = await bot.get_chat_member(
                chat_id=channel1_id,
                user_id=user_id
            )
            subscribed1 = member1.status in ['member', 'administrator', 'creator']
            logger.info(f"   ✅ Канал 1 (ID {channel1_id}): статус={member1.status}, подписан={subscribed1}")
            channel1_checked = True
        except Exception as e:
            logger.warning(f"   ⚠️ Ошибка проверки канала 1 по ID ({channel1_id}): {e}")
        
        # Если не получилось по ID, пробуем через username
        if not channel1_checked and hasattr(settings, 'CHANNEL1_USERNAME') and settings.CHANNEL1_USERNAME:
            try:
                username = settings.CHANNEL1_USERNAME.replace('@', '').strip()
                if not username.startswith('@'):
                    username = f"@{username}"
                logger.info(f"   🔄 Пробуем канал 1 через username: {username}")
                member1 = await bot.get_chat_member(chat_id=username, user_id=user_id)
                subscribed1 = member1.status in ['member', 'administrator', 'creator']
                logger.info(f"   ✅ Канал 1 (через username {username}): статус={member1.status}, подписан={subscribed1}")
                channel1_checked = True
            except Exception as e2:
                logger.error(f"   ❌ Ошибка проверки канала 1 через username: {e2}")
        
        if not channel1_checked:
            subscribed1 = False
        
        # Проверяем второй канал
        subscribed2 = False
        channel2_checked = False
        
        # Сначала пробуем по ID
        try:
            member2 = await bot.get_chat_member(
                chat_id=channel2_id,
                user_id=user_id
            )
            subscribed2 = member2.status in ['member', 'administrator', 'creator']
            logger.info(f"   ✅ Канал 2 (ID {channel2_id}): статус={member2.status}, подписан={subscribed2}")
            channel2_checked = True
        except Exception as e:
            logger.warning(f"   ⚠️ Ошибка проверки канала 2 по ID ({channel2_id}): {e}")
        
        # Если не получилось по ID, пробуем через username
        if not channel2_checked and hasattr(settings, 'CHANNEL2_USERNAME') and settings.CHANNEL2_USERNAME:
            try:
                username = settings.CHANNEL2_USERNAME.replace('@', '').strip()
                if not username.startswith('@'):
                    username = f"@{username}"
                logger.info(f"   🔄 Пробуем канал 2 через username: {username}")
                member2 = await bot.get_chat_member(chat_id=username, user_id=user_id)
                subscribed2 = member2.status in ['member', 'administrator', 'creator']
                logger.info(f"   ✅ Канал 2 (через username {username}): статус={member2.status}, подписан={subscribed2}")
                channel2_checked = True
            except Exception as e2:
                logger.error(f"   ❌ Ошибка проверки канала 2 через username: {e2}")
        
        if not channel2_checked:
            subscribed2 = False
        
        result = subscribed1 and subscribed2
        logger.info(f"   📊 Результат проверки: {result} (канал1={subscribed1}, канал2={subscribed2})")
        return result
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при проверке подписки: {e}", exc_info=True)
        return False


def is_admin(user_id: int) -> bool:
    """
    Проверка, является ли пользователь администратором
    
    Args:
        user_id: ID пользователя
        
    Returns:
        True если администратор, иначе False
    """
    return user_id in settings.admin_ids_list


def validate_text(text: str, max_length: int = 4096) -> bool:
    """
    Валидация текста
    
    Args:
        text: Текст для проверки
        max_length: Максимальная длина
        
    Returns:
        True если валиден, иначе False
    """
    if not text or not isinstance(text, str):
        return False
    if len(text.strip()) == 0:
        return False
    if len(text) > max_length:
        return False
    return True


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Очистка пользовательского ввода
    
    Args:
        text: Входной текст
        max_length: Максимальная длина
        
    Returns:
        Очищенный текст
    """
    if not text:
        return ""
    # Убираем лишние пробелы и ограничиваем длину
    cleaned = text.strip()[:max_length]
    # Удаляем потенциально опасные символы (базовая защита)
    cleaned = cleaned.replace('\x00', '')  # Null bytes
    return cleaned


def validate_message_size(message) -> bool:
    """
    Валидация размера сообщения
    
    Args:
        message: Объект сообщения
        
    Returns:
        True если размер допустим, иначе False
    """
    # Проверка текста
    if message.text and len(message.text) > 4096:
        return False
    
    # Проверка caption
    if message.caption and len(message.caption) > 1024:
        return False
    
    # Проверка размера файлов (если есть)
    if hasattr(message, 'document') and message.document:
        # Максимальный размер файла 50MB (Telegram limit)
        if message.document.file_size and message.document.file_size > 50 * 1024 * 1024:
            return False
    
    return True

