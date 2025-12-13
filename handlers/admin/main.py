"""
Главная админ-панель
"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.validators import is_admin
from utils.keyboards import create_admin_keyboard

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет прав администратора")
        return
    
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

