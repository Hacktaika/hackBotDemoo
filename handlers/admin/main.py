"""
Главная админ-панель
"""
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.validators import is_admin
from utils.keyboards import create_admin_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ-панель"""
    logger.info(f"📋 /admin от пользователя {message.from_user.id}")
    
    if not is_admin(message.from_user.id):
        logger.info(f"❌ Пользователь {message.from_user.id} не админ")
        await message.answer("❌ У тебя нет прав администратора")
        return
    
    logger.info(f"✅ Показываем админ-панель для {message.from_user.id}")
    keyboard = create_admin_keyboard()
    
    await message.answer(
        "🔐 Админ-панель\n\n"
        "Выбери действие:",
        reply_markup=keyboard
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущей операции"""
    await state.clear()
    await message.answer("❌ Операция отменена")

