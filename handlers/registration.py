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
from utils.validators import sanitize_input, check_channel_subscription, validate_message_size
from utils.rate_limit import check_registration_rate_limit
from utils.keyboards import create_source_keyboard
from utils.subscription import show_subscription_request
from handlers.menu import show_main_menu
from utils.video_notes import get_video_note

router = Router()
logger = logging.getLogger(__name__)


class RegistrationStates(StatesGroup):
    """Состояния опросника"""
    waiting_name = State()
    waiting_position = State()
    waiting_expectations = State()
    waiting_source = State()


async def send_question(message: Message, state: FSMContext, video_note_key: str, text: str, keyboard=None):
    """Отправить вопрос в зависимости от выбранного формата"""
    data = await state.get_data()
    survey_format = data.get("survey_format", "text")
    video_note_id = get_video_note(video_note_key)
    
    if survey_format == "video" and video_note_id:
        await message.answer_video_note(video_note=video_note_id)
        if keyboard:
            await message.answer("👆 Выбери вариант:", reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


@router.message(RegistrationStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    user_id = message.from_user.id
    
    # Проверка rate limit
    allowed, error_msg = check_registration_rate_limit(user_id)
    if not allowed:
        logger.warning(f"🚫 Пользователь {user_id} превысил лимит регистрации")
        await message.answer(error_msg)
        return
    
    # Валидация размера сообщения
    if not validate_message_size(message):
        await message.answer("❌ Сообщение слишком большое. Пожалуйста, отправь более короткий текст.")
        return
    
    # Если получено видео, пропускаем вопрос
    if message.video or message.video_note:
        logger.info(f"📹 Получено видео, пропускаем вопрос имени для пользователя {user_id}")
        default_name = message.from_user.first_name or "Пользователь"
        await state.update_data(name=default_name)
        await state.set_state(RegistrationStates.waiting_position)
        await send_question(message, state, "position", "💼 Чем занимаешься? Какая должность в компании?")
        return
    
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текстовое сообщение")
        return
    
    name = sanitize_input(message.text, max_length=100)
    if not name or len(name) < 2:
        await message.answer("❌ Пожалуйста, введи свое имя (минимум 2 символа)")
        return
    
    if len(name) > 100:
        await message.answer("❌ Имя слишком длинное. Максимум 100 символов.")
        return
    
    await state.update_data(name=name)
    await state.set_state(RegistrationStates.waiting_position)
    await send_question(message, state, "position", "💼 Чем занимаешься? Какая должность в компании?")


@router.message(RegistrationStates.waiting_position)
async def process_position(message: Message, state: FSMContext):
    """Обработка должности"""
    # Валидация размера сообщения
    if not validate_message_size(message):
        await message.answer("❌ Сообщение слишком большое. Пожалуйста, отправь более короткий текст.")
        return
    
    # Если получено видео, пропускаем вопрос
    if message.video or message.video_note:
        logger.info(f"📹 Получено видео, пропускаем вопрос должности для пользователя {message.from_user.id}")
        await state.update_data(position="Не указано")
        await state.set_state(RegistrationStates.waiting_expectations)
        await send_question(message, state, "expectations", "🎯 Что ты хочешь получить от этого бота? Какую пользу?")
        return
    
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текстовое сообщение")
        return
    
    position = sanitize_input(message.text, max_length=200)
    if not position or len(position) < 3:
        await message.answer("❌ Пожалуйста, укажи свою должность (минимум 3 символа)")
        return
    
    if len(position) > 200:
        await message.answer("❌ Описание должности слишком длинное. Максимум 200 символов.")
        return
    
    await state.update_data(position=position)
    await state.set_state(RegistrationStates.waiting_expectations)
    await send_question(message, state, "expectations", "🎯 Что ты хочешь получить от этого бота? Какую пользу?")


@router.message(RegistrationStates.waiting_expectations)
async def process_expectations(message: Message, state: FSMContext):
    """Обработка ожиданий"""
    keyboard = create_source_keyboard()
    
    # Валидация размера сообщения
    if not validate_message_size(message):
        await message.answer("❌ Сообщение слишком большое. Пожалуйста, отправь более короткий текст.")
        return
    
    # Если получено видео, пропускаем вопрос
    if message.video or message.video_note:
        logger.info(f"📹 Получено видео, пропускаем вопрос ожиданий для пользователя {message.from_user.id}")
        await state.update_data(expectations="Не указано")
        await state.set_state(RegistrationStates.waiting_source)
        await send_question(message, state, "source", "📬 Как ты узнал о боте?", keyboard)
        return
    
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текстовое сообщение")
        return
    
    expectations = sanitize_input(message.text, max_length=500)
    if not expectations or len(expectations) < 5:
        await message.answer("❌ Пожалуйста, опиши свои ожидания подробнее (минимум 5 символов)")
        return
    
    if len(expectations) > 500:
        await message.answer("❌ Описание слишком длинное. Максимум 500 символов.")
        return
    
    await state.update_data(expectations=expectations)
    await state.set_state(RegistrationStates.waiting_source)
    await send_question(message, state, "source", "📬 Как ты узнал о боте?", keyboard)


@router.message(RegistrationStates.waiting_source)
async def process_source_video(message: Message, state: FSMContext):
    """Обработка источника при получении видео"""
    # Если получено видео, автоматически выбираем "Другие источники"
    if message.video or message.video_note:
        logger.info(f"📹 Получено видео, автоматически выбираем источник для пользователя {message.from_user.id}")
        await state.update_data(source="Другие источники")
        
        # Завершаем опросник
        data = await state.get_data()
        user_id = message.from_user.id
        logger.info(f"✅ Пользователь {user_id} завершил опросник")
        
        db = get_db_session()
        
        try:
            # Сохраняем данные пользователя
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user:
                logger.info(f"👤 Создание нового пользователя {user_id}")
                user = User(
                    telegram_id=user_id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name
                )
                db.add(user)
            
            user.name = data.get('name')
            user.position = data.get('position')
            user.expectations = data.get('expectations')
            user.source = data.get('source')
            user.is_registered = True
            
            db.commit()
            logger.info(f"💾 Данные пользователя {user_id} сохранены")
            
            # Отправляем финальный кружочек (если видео-формат)
            data_format = data.get("survey_format", "text")
            finish_note = get_video_note("finish")
            if data_format == "video" and finish_note:
                await message.answer_video_note(video_note=finish_note)
            
            # Проверяем подписку после опроса
            bot = message.bot
            is_subscribed = await check_channel_subscription(bot, user_id)
            
            if is_subscribed:
                user.is_subscribed = True
                db.commit()
                await show_main_menu(message, db, user, edit=False)
            else:
                user.is_subscribed = False
                db.commit()
                await show_subscription_request(message, bot, edit=False)
                
        finally:
            db.close()
            await state.clear()


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
        
        # Отправляем финальный кружочек (если видео-формат)
        finish_note = get_video_note("finish")
        if data.get("survey_format") == "video" and finish_note:
            await callback.message.answer_video_note(video_note=finish_note)
        
        # Проверяем подписку после опроса
        bot = callback.bot
        is_subscribed = await check_channel_subscription(bot, user_id)
        
        if is_subscribed:
            user.is_subscribed = True
            db.commit()
            await show_main_menu(callback.message, db, user, edit=False)
        else:
            user.is_subscribed = False
            db.commit()
            await show_subscription_request(callback.message, bot, edit=False)
            
    finally:
        db.close()
        await state.clear()

