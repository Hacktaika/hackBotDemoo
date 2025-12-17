"""
Утилиты для работы с каналами Telegram
"""
import logging
from aiogram import Bot

logger = logging.getLogger(__name__)


async def get_channel_id_by_username(bot: Bot, username: str) -> int:
    """
    Получить ID канала по username
    
    Args:
        bot: Экземпляр бота
        username: Username канала (с @ или без)
        
    Returns:
        ID канала в формате -100XXXXXXXXXX или None если не удалось
    """
    try:
        # Убираем @ если есть
        username = username.replace('@', '').strip()
        if not username.startswith('@'):
            username = f"@{username}"
        
        chat = await bot.get_chat(username)
        logger.info(f"📡 Получен ID канала {username}: {chat.id}")
        return chat.id
    except Exception as e:
        logger.error(f"❌ Ошибка получения ID канала {username}: {e}")
        return None


async def verify_channel_access(bot: Bot, channel_id) -> bool:
    """
    Проверить доступ бота к каналу
    
    Args:
        bot: Экземпляр бота
        channel_id: ID канала
        
    Returns:
        True если бот имеет доступ, иначе False
    """
    try:
        bot_info = await bot.get_me()
        member = await bot.get_chat_member(chat_id=channel_id, user_id=bot_info.id)
        logger.info(f"🤖 Бот в канале {channel_id}: статус={member.status}")
        return member.status in ['administrator', 'creator', 'member']
    except Exception as e:
        logger.error(f"❌ Бот не имеет доступа к каналу {channel_id}: {e}")
        return False




