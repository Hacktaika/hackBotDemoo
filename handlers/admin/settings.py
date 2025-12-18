"""
Управление настройками (PDF, фото меню и т.д.)
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.validators import is_admin
from handlers.quiz import PDF_FILE_ID as QUIZ_PDF_FILE_ID
from config import MENU_PHOTO_FILE_ID

router = Router()
logger = logging.getLogger(__name__)


class SettingsStates(StatesGroup):
    """Состояния управления настройками"""
    waiting_pdf_file = State()
    waiting_menu_photo = State()


@router.callback_query(F.data == "admin_settings")
async def settings_menu(callback: CallbackQuery):
    """Меню настроек"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    
    # Получаем текущие значения
    pdf_status = "✅ Установлен" if QUIZ_PDF_FILE_ID else "❌ Не установлен"
    photo_status = "✅ Установлено" if MENU_PHOTO_FILE_ID else "❌ Не установлено"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 PDF для викторины", callback_data="admin_set_pdf")],
        [InlineKeyboardButton(text="🖼 Фото для меню", callback_data="admin_set_menu_photo")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])
    
    text = (
        f"⚙️ <b>Настройки</b>\n\n"
        f"📄 PDF для викторины: {pdf_status}\n"
        f"🖼 Фото для меню: {photo_status}\n\n"
        f"Выбери что изменить:"
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "admin_set_pdf")
async def set_pdf_start(callback: CallbackQuery, state: FSMContext):
    """Начать установку PDF файла"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(SettingsStates.waiting_pdf_file)
    
    current_status = f"Текущий file_id: <code>{QUIZ_PDF_FILE_ID}</code>" if QUIZ_PDF_FILE_ID else "PDF не установлен"
    
    await callback.message.edit_text(
        f"📄 <b>Установка PDF для викторины</b>\n\n"
        f"{current_status}\n\n"
        f"Отправь PDF файл боту, чтобы получить file_id.\n"
        f"Затем скопируй file_id и обнови его в файле handlers/quiz.py\n"
        f"в переменной PDF_FILE_ID.",
        parse_mode="HTML"
    )


@router.message(SettingsStates.waiting_pdf_file)
async def process_pdf_file(message: Message, state: FSMContext):
    """Обработка PDF файла"""
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "Неизвестно"
        
        await message.answer(
            f"📄 <b>File ID PDF файла:</b>\n\n"
            f"Имя файла: <code>{file_name}</code>\n"
            f"File ID: <code>{file_id}</code>\n\n"
            f"Скопируй этот file_id и обнови его в файле:\n"
            f"<code>handlers/quiz.py</code>\n"
            f"в переменной <code>PDF_FILE_ID</code>",
            parse_mode="HTML"
        )
        logger.info(f"📄 Админ {message.from_user.id} получил file_id PDF: {file_id}")
    else:
        await message.answer("❌ Отправь PDF файл (документ)")
    
    await state.clear()


@router.callback_query(F.data == "admin_set_menu_photo")
async def set_menu_photo_start(callback: CallbackQuery, state: FSMContext):
    """Начать установку фото для меню"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(SettingsStates.waiting_menu_photo)
    
    current_status = f"Текущий file_id: <code>{MENU_PHOTO_FILE_ID}</code>" if MENU_PHOTO_FILE_ID else "Фото не установлено"
    
    await callback.message.edit_text(
        f"🖼 <b>Установка фото для меню</b>\n\n"
        f"{current_status}\n\n"
        f"Отправь фото боту, чтобы получить file_id.\n"
        f"Затем скопируй file_id и обнови его в файле config.py\n"
        f"в переменной MENU_PHOTO_FILE_ID.",
        parse_mode="HTML"
    )


@router.message(SettingsStates.waiting_menu_photo)
async def process_menu_photo(message: Message, state: FSMContext):
    """Обработка фото для меню"""
    if message.photo:
        file_id = message.photo[-1].file_id
        
        await message.answer(
            f"🖼 <b>File ID фото:</b>\n\n"
            f"<code>{file_id}</code>\n\n"
            f"Скопируй этот file_id и обнови его в файле:\n"
            f"<code>config.py</code>\n"
            f"в переменной <code>MENU_PHOTO_FILE_ID</code>",
            parse_mode="HTML"
        )
        logger.info(f"🖼 Админ {message.from_user.id} получил file_id фото меню: {file_id}")
    else:
        await message.answer("❌ Отправь фото")
    
    await state.clear()

