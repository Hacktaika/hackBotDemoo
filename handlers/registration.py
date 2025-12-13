"""
Обработчик опросника регистрации
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_db_session
from database.models import User
from utils.validators import sanitize_input, check_channel_subscription
from utils.keyboards import create_source_keyboard
from utils.subscription import show_subscription_request
from handlers.menu import show_main_menu

router = Router()
logger = logging.getLogger(__name__)


class RegistrationStates(StatesGroup):
    """Состояния опросника"""
    waiting_name = State()
    waiting_position = State()
    waiting_expectations = State()
    waiting_source = State()


@router.message(RegistrationStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    name = sanitize_input(message.text)
    if not name or len(name) < 2:
        await message.answer("❌ Пожалуйста, введи свое имя (минимум 2 символа)")
        return
    
    await state.update_data(name=name)
    await state.set_state(RegistrationStates.waiting_position)
    await message.answer("💼 Чем занимаешься? Какая должность в компании?")


@router.message(RegistrationStates.waiting_position)
async def process_position(message: Message, state: FSMContext):
    """Обработка должности"""
    position = sanitize_input(message.text)
    if not position or len(position) < 3:
        await message.answer("❌ Пожалуйста, укажи свою должность (минимум 3 символа)")
        return
    
    await state.update_data(position=position)
    await state.set_state(RegistrationStates.waiting_expectations)
    await message.answer("🎯 Что ты хочешь получить от этого бота? Какую пользу?")


@router.message(RegistrationStates.waiting_expectations)
async def process_expectations(message: Message, state: FSMContext):
    """Обработка ожиданий"""
    expectations = sanitize_input(message.text)
    if not expectations or len(expectations) < 5:
        await message.answer("❌ Пожалуйста, опиши свои ожидания подробнее (минимум 5 символов)")
        return
    
    await state.update_data(expectations=expectations)
    await state.set_state(RegistrationStates.waiting_source)
    
    keyboard = create_source_keyboard()
    
    await message.answer(
        "📬 Как ты узнал о боте?",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("source_"))
async def process_source(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора источника"""
    source_map = {
        "source_social": "Соцсети",
        "source_word_of_mouth": "Сарафанка",
        "source_website": "На сайте",
        "source_other": "Другие источники"
    }
    
    source = source_map.get(callback.data, "Другие источники")
    await state.update_data(source=source)
    
    await callback.answer()
    await callback.message.delete()
    
    # Завершаем опросник
    data = await state.get_data()
    user_id = callback.from_user.id
    logger.info(f"✅ Пользователь {user_id} завершил опросник")
    
    db = get_db_session()
    
    try:
        # Сохраняем данные пользователя
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            logger.info(f"👤 Создание нового пользователя {user_id}")
            user = User(
                telegram_id=user_id,
                username=callback.from_user.username,
                first_name=callback.from_user.first_name,
                last_name=callback.from_user.last_name
            )
            db.add(user)
        
        user.name = data.get('name')
        user.position = data.get('position')
        user.expectations = data.get('expectations')
        user.source = data.get('source')
        user.is_registered = True
        
        db.commit()
        logger.info(f"💾 Данные пользователя {user_id} сохранены")
        
        # Проверяем подписку
        bot = callback.bot
        logger.info(f"🔍 Проверка подписки пользователя {user_id}...")
        is_subscribed = await check_channel_subscription(bot, user_id)
        
        if is_subscribed:
            logger.info(f"✅ Пользователь {user_id} подписан на оба канала")
            user.is_subscribed = True
            db.commit()
            # Показываем меню, редактируя существующее сообщение
            await show_main_menu(callback.message, db, user, edit=True)
        else:
            logger.info(f"⚠️ Пользователь {user_id} не подписан на каналы")
            user.is_subscribed = False
            db.commit()
            # Отправляем сообщение с кнопками подписки (редактируем если возможно)
            await show_subscription_request(callback.message, bot, edit=True)
            
    finally:
        db.close()
        await state.clear()

