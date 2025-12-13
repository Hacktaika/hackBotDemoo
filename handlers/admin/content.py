"""
Управление контентом
"""
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_db_session
from database.models import Content
from utils.validators import is_admin, validate_text

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
    keyword = message.text.strip().lower()
    
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
    if message.text and message.text.strip() == "/skip":
        text = None
    else:
        text = message.text if message.text else None
    
    await state.update_data(text=text)
    await state.set_state(ContentStates.waiting_content_file)
    await message.answer(
        "📎 Отправь файл (фото, видео или документ) или отправь /skip для текстового контента:"
    )


@router.message(ContentStates.waiting_content_file)
async def process_content_file(message: Message, state: FSMContext):
    """Обработка файла контента"""
    data = await state.get_data()
    keyword = data.get('keyword')
    text = data.get('text')
    
    content_type = "text"
    file_id = None
    
    if message.photo:
        content_type = "photo"
        file_id = message.photo[-1].file_id
        if not text:
            text = message.caption
    elif message.video:
        content_type = "video"
        file_id = message.video.file_id
        if not text:
            text = message.caption
    elif message.document:
        content_type = "document"
        file_id = message.document.file_id
        if not text:
            text = message.caption
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

