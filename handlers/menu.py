"""
Обработчик главного меню
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from database.models import User
from database.db import get_db_session
from config import MENU_PHOTO_FILE_ID

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
    
    # Кнопка демо проектов
    keyboard_buttons.append([InlineKeyboardButton(text="📦 Демо проекты", callback_data="demo_projects")])
    
    # Кнопка викторины (PDF бонус) - только если пользователь еще не получил
    if not user.has_pdf:
        keyboard_buttons.append([InlineKeyboardButton(text="🎯 ПОЛУЧИТЬ БОНУС", callback_data="quiz_start")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    text = (
        "🎉 Добро пожаловать в главное меню!\n\n"
        "Здесь ты можешь:\n"
        "• Узнать больше о ХакТайке\n"
        "• Познакомиться с основателем\n"
        "• Посмотреть демо проекты\n"
        "• Получить бонусы\n\n"
        "Выбери, что тебя интересует:"
    )
    
    # Пытаемся отредактировать существующее сообщение, если указано
    if edit:
        try:
            # Если есть фото, удаляем старое сообщение и отправляем новое с фото
            if MENU_PHOTO_FILE_ID:
                await message.delete()
                await message.answer_photo(
                    photo=MENU_PHOTO_FILE_ID,
                    caption=text,
                    reply_markup=keyboard
                )
                return
            else:
                await message.edit_text(text, reply_markup=keyboard)
                return
        except Exception:
            pass
    
    # Отправляем новое сообщение
    if MENU_PHOTO_FILE_ID:
        await message.answer_photo(
            photo=MENU_PHOTO_FILE_ID,
            caption=text,
            reply_markup=keyboard
        )
    else:
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
