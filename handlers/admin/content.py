"""
Управление контентом
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_db_session
from database.models import Content
from utils.validators import is_admin, validate_text, validate_message_size
from utils.rate_limit import check_admin_rate_limit

router = Router()


class ContentStates(StatesGroup):
    """Состояния добавления контента"""
    waiting_content_keyword = State()
    waiting_content_text = State()
    waiting_content_file = State()


@router.callback_query(F.data == "admin_add_content")
async def add_content_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление контента"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(ContentStates.waiting_content_keyword)
    await callback.message.answer("➕ Введи ключевое слово для контента:")


@router.message(ContentStates.waiting_content_keyword)
async def process_content_keyword(message: Message, state: FSMContext):
    """Обработка ключевого слова"""
    admin_id = message.from_user.id
    
    # Проверка rate limit для админов
    allowed, error_msg = check_admin_rate_limit(admin_id)
    if not allowed:
        await message.answer(error_msg)
        return
    
    # Валидация размера сообщения
    if not validate_message_size(message):
        await message.answer("❌ Сообщение слишком большое")
        return
    
    if not message.text:
        await message.answer("❌ Пожалуйста, отправь текстовое сообщение")
        return
    
    keyword = message.text.strip().lower()
    
    # Ограничение длины ключевого слова
    if len(keyword) > 255:
        await message.answer("❌ Ключевое слово слишком длинное (максимум 255 символов)")
        return
    
    if not validate_text(keyword, max_length=255):
        await message.answer("❌ Некорректное ключевое слово")
        return
    
    db = get_db_session()
    try:
        # Проверяем, не существует ли уже
        existing = db.query(Content).filter(Content.keyword == keyword).first()
        if existing:
            await message.answer("❌ Контент с таким ключевым словом уже существует")
            return
        
        await state.update_data(keyword=keyword)
        await state.set_state(ContentStates.waiting_content_text)
        await message.answer("📝 Введи текст контента (или отправь /skip чтобы пропустить):")
    finally:
        db.close()


@router.message(ContentStates.waiting_content_text)
async def process_content_text(message: Message, state: FSMContext):
    """Обработка текста контента"""
    # Валидация размера сообщения
    if not validate_message_size(message):
        await message.answer("❌ Сообщение слишком большое. Максимальный размер текста: 4096 символов.")
        return
    
    if message.text and message.text.strip() == "/skip":
        text = None
        entities = None
    else:
        # Сохраняем текст с HTML-форматированием, ограничиваем размер
        if message.text:
            raw_text = message.html_text or message.text
            # Ограничиваем до 4096 символов (лимит Telegram)
            text = raw_text[:4096] if len(raw_text) > 4096 else raw_text
        else:
            text = None
        entities = None
    
    await state.update_data(text=text)
    await state.set_state(ContentStates.waiting_content_file)
    await message.answer(
        "📎 Отправь файл (фото, видео или документ) или отправь /skip для текстового контента:"
    )


@router.message(ContentStates.waiting_content_file)
async def process_content_file(message: Message, state: FSMContext):
    """Обработка файла контента"""
    # Валидация размера сообщения
    if not validate_message_size(message):
        await message.answer("❌ Файл или сообщение слишком большое")
        return
    
    data = await state.get_data()
    keyword = data.get('keyword')
    text = data.get('text')
    
    content_type = "text"
    file_id = None
    
    if message.photo:
        content_type = "photo"
        file_id = message.photo[-1].file_id
        if not text and message.caption:
            # Ограничиваем caption до 1024 символов
            text = message.caption[:1024]
    elif message.video:
        content_type = "video"
        file_id = message.video.file_id
        if not text and message.caption:
            text = message.caption[:1024]
    elif message.document:
        # Проверяем размер документа
        if message.document.file_size and message.document.file_size > 50 * 1024 * 1024:
            await message.answer("❌ Файл слишком большой. Максимальный размер: 50MB")
            return
        content_type = "document"
        file_id = message.document.file_id
        if not text and message.caption:
            text = message.caption[:1024]
    elif message.text and message.text.strip() == "/skip":
        content_type = "text"
    else:
        await message.answer("❌ Отправь файл или /skip")
        return
    
    db = get_db_session()
    try:
        content = Content(
            keyword=keyword,
            content_type=content_type,
            text=text,
            file_id=file_id
        )
        db.add(content)
        db.commit()
        
        await message.answer(f"✅ Контент добавлен!\n\nКлючевое слово: {keyword}")
    finally:
        db.close()
        await state.clear()

