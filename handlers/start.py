"""
Обработчик команды /start
"""
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from database.db import get_db_session
from database.models import User
from handlers.menu import show_main_menu
from handlers.registration import RegistrationStates

router = Router()
logger = logging.getLogger(__name__)


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
            # Пользователь уже зарегистрирован - показываем меню (новое сообщение)
            await state.clear()
            await show_main_menu(message, db, user, edit=False)
            return
        
        logger.info(f"🆕 Новый пользователь {user_id}, начинаем опросник")
        # Начинаем опросник
        await state.set_state(RegistrationStates.waiting_name)
        await message.answer(
            "👋 Привет! Скажи, как тебя зовут?",
            reply_markup=None
        )
    finally:
        db.close()

