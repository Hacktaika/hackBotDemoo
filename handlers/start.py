"""
Обработчик команды /start
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from database.db import get_db_session
from database.models import User
from handlers.menu import show_main_menu
from handlers.registration import RegistrationStates
from config import ADMIN_IDS
from utils.video_notes import get_video_note
from utils.validators import check_channel_subscription
from utils.subscription import show_subscription_request

router = Router()
logger = logging.getLogger(__name__)


def get_format_keyboard():
    """Клавиатура выбора формата опроса"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Видео-формат", callback_data="format_video")],
        [InlineKeyboardButton(text="📝 Текстовый формат", callback_data="format_text")]
    ])


@router.message(F.video_note)
async def get_video_note_id(message: Message, state: FSMContext):
    """Получить file_id кружочка (только для админов)"""
    logger.info(f"📹 Получен кружочек от {message.from_user.id}")
    current_state = await state.get_state()
    logger.info(f"   Текущее состояние FSM: {current_state}")
    
    if current_state is None:
        file_id = message.video_note.file_id
        await message.answer(f"📹 File ID кружочка:\n\n<code>{file_id}</code>", parse_mode="HTML")
        logger.info(f"Video note file_id: {file_id}")


@router.message(F.photo)
async def get_photo_id(message: Message, state: FSMContext):
    """Получить file_id фото (для админов)"""
    current_state = await state.get_state()
    if current_state is None and message.from_user.id in ADMIN_IDS:
        file_id = message.photo[-1].file_id
        await message.answer(f"🖼 File ID фото:\n\n<code>{file_id}</code>", parse_mode="HTML")
        logger.info(f"Photo file_id: {file_id}")


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    logger.info(f"📨 /start от пользователя {username} (ID: {user_id})")
    
    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if user and user.is_registered:
            logger.info(f"✅ Пользователь {user_id} уже зарегистрирован, показываем меню")
            await state.clear()
            await show_main_menu(message, db, user, edit=False)
            return
        
        logger.info(f"🆕 Новый пользователь {user_id}, показываем выбор формата")
        # Показываем выбор формата опроса
        await message.answer(
            "👋 Привет! Пройди короткий опрос.\n\nВыбери удобный формат:",
            reply_markup=get_format_keyboard()
        )
    finally:
        db.close()


@router.callback_query(F.data == "format_video")
async def start_video_format(callback: CallbackQuery, state: FSMContext):
    """Начать опрос в видео-формате"""
    await callback.answer()
    await callback.message.delete()
    
    await state.update_data(survey_format="video")
    await state.set_state(RegistrationStates.waiting_name)
    
    video_note = get_video_note("name")
    if video_note:
        await callback.message.answer_video_note(video_note=video_note)
    else:
        await callback.message.answer("👋 Привет! Скажи, как тебя зовут?")


@router.callback_query(F.data == "format_text")
async def start_text_format(callback: CallbackQuery, state: FSMContext):
    """Начать опрос в текстовом формате"""
    await callback.answer()
    await callback.message.delete()
    
    await state.update_data(survey_format="text")
    await state.set_state(RegistrationStates.waiting_name)
    
    await callback.message.answer("👋 Привет! Скажи, как тебя зовут?")

