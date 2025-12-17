"""
Обработчик викторины
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from utils.keyboards import create_back_button

router = Router()


@router.callback_query(F.data == "quiz_start")
async def start_quiz(callback: CallbackQuery):
    """Начать викторину (заглушка)"""
    await callback.answer()
    
    keyboard = create_back_button()
    
    await callback.message.edit_text(
        "🎯 Викторина\n\n"
        "Здесь будет викторина с вопросами и заданиями.\n"
        "Функционал в разработке...",
        reply_markup=keyboard
    )




