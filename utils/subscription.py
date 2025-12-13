"""
Утилиты для работы с подписками
"""
from aiogram.types import Message
from aiogram import Bot
from utils.validators import check_channel_subscription
from utils.keyboards import create_subscription_keyboard


async def show_subscription_request(message: Message, bot: Bot, edit: bool = False):
    """
    Показать запрос на подписку
    
    Args:
        message: Сообщение для редактирования/ответа
        bot: Экземпляр бота
        edit: Редактировать существующее сообщение или отправить новое
    """
    keyboard = create_subscription_keyboard()
    text = "📢 Подпишись на наши каналы, чтобы получить доступ к бонусам и материалам!"
    
    # Всегда пытаемся отредактировать существующее сообщение
    try:
        await message.edit_text(text, reply_markup=keyboard)
    except Exception:
        # Если не удалось отредактировать (сообщение не существует или изменилось), отправляем новое
        if not edit:  # Только если это не попытка редактирования
            await message.answer(text, reply_markup=keyboard)

