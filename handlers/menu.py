"""
Обработчик главного меню
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from database.models import User
from database.db import get_db_session

router = Router()


async def show_main_menu(message: Message, db: Session, user: User, edit: bool = False):
    """
    Показать главное меню
    
    Args:
        message: Сообщение для редактирования/ответа
        db: Сессия БД
        user: Пользователь
        edit: Редактировать существующее сообщение вместо создания нового
    """
    # Формируем кнопки
    keyboard_buttons = []
    
    # Информационные кнопки
    keyboard_buttons.append([InlineKeyboardButton(text="🦅 ХакТайка", callback_data="info_hacktaika")])
    keyboard_buttons.append([InlineKeyboardButton(text="👤 Основатель", callback_data="info_founder")])
    
    # Кнопка викторины
    keyboard_buttons.append([InlineKeyboardButton(text="🎯 ПОЛУЧИТЬ БОНУС", callback_data="quiz_start")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    text = (
        "🎉 Добро пожаловать в главное меню!\n\n"
        "Здесь ты можешь:\n"
        "• Узнать больше о ХакТайке\n"
        "• Познакомиться с основателем\n"
        "• Получить бонусы\n\n"
        "Выбери, что тебя интересует:"
    )
    
    # Пытаемся отредактировать существующее сообщение, если указано
    if edit:
        try:
            await message.edit_text(text, reply_markup=keyboard)
            return
        except Exception:
            pass
    
    # Отправляем новое сообщение
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "menu_main")
async def back_to_menu(callback: CallbackQuery):
    """Вернуться в главное меню"""
    await callback.answer()
    
    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == callback.from_user.id).first()
        if user:
            await show_main_menu(callback.message, db, user, edit=True)
    finally:
        db.close()
