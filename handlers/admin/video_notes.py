"""
Админка для управления кружочками опроса
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.validators import is_admin
from utils.video_notes import get_video_notes, set_video_note, delete_video_note, VIDEO_NOTE_KEYS

router = Router()
logger = logging.getLogger(__name__)


class VideoNoteStates(StatesGroup):
    """Состояния для установки кружочка"""
    waiting_video_note = State()


def get_video_notes_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления кружочками"""
    notes = get_video_notes()
    buttons = []
    
    for key, name in VIDEO_NOTE_KEYS.items():
        status = "✅" if notes.get(key) else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {name}",
            callback_data=f"vn_edit_{key}"
        )])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_edit_keyboard(key: str) -> InlineKeyboardMarkup:
    """Клавиатура редактирования кружочка"""
    notes = get_video_notes()
    buttons = [[InlineKeyboardButton(text="📹 Установить кружочек", callback_data=f"vn_set_{key}")]]
    
    if notes.get(key):
        buttons.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"vn_del_{key}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_video_notes")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "admin_video_notes")
async def show_video_notes(callback: CallbackQuery):
    """Показать список кружочков"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "🎬 <b>Кружочки для опроса</b>\n\n"
        "✅ — кружочек установлен\n"
        "❌ — не установлен\n\n"
        "Нажми на пункт для редактирования:",
        reply_markup=get_video_notes_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("vn_edit_"))
async def edit_video_note(callback: CallbackQuery):
    """Показать меню редактирования кружочка"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    key = callback.data.replace("vn_edit_", "")
    name = VIDEO_NOTE_KEYS.get(key, key)
    notes = get_video_notes()
    
    status = "✅ Установлен" if notes.get(key) else "❌ Не установлен"
    
    await callback.answer()
    await callback.message.edit_text(
        f"🎬 <b>{name}</b>\n\n"
        f"Статус: {status}",
        reply_markup=get_edit_keyboard(key),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("vn_set_"))
async def start_set_video_note(callback: CallbackQuery, state: FSMContext):
    """Начать установку кружочка"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    key = callback.data.replace("vn_set_", "")
    name = VIDEO_NOTE_KEYS.get(key, key)
    
    await state.update_data(video_note_key=key)
    await state.set_state(VideoNoteStates.waiting_video_note)
    
    await callback.answer()
    await callback.message.edit_text(
        f"📹 <b>Установка кружочка</b>\n\n"
        f"Вопрос: {name}\n\n"
        f"Отправь кружочек (video note) для этого вопроса.\n\n"
        f"Для отмены отправь /cancel",
        parse_mode="HTML"
    )


@router.message(VideoNoteStates.waiting_video_note, F.video_note)
async def receive_video_note(message: Message, state: FSMContext):
    """Получить и сохранить кружочек"""
    if not is_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    key = data.get("video_note_key")
    
    if not key:
        await state.clear()
        return
    
    file_id = message.video_note.file_id
    set_video_note(key, file_id)
    
    name = VIDEO_NOTE_KEYS.get(key, key)
    logger.info(f"✅ Кружочек '{key}' установлен: {file_id[:20]}...")
    
    await state.clear()
    await message.answer(
        f"✅ Кружочек для «{name}» успешно установлен!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ К списку кружочков", callback_data="admin_video_notes")]
        ])
    )


@router.message(VideoNoteStates.waiting_video_note)
async def wrong_content_type(message: Message):
    """Неправильный тип контента"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer("❌ Отправь именно кружочек (video note), а не обычное видео или фото")


@router.callback_query(F.data.startswith("vn_del_"))
async def delete_video_note_handler(callback: CallbackQuery):
    """Удалить кружочек"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    key = callback.data.replace("vn_del_", "")
    name = VIDEO_NOTE_KEYS.get(key, key)
    
    delete_video_note(key)
    logger.info(f"🗑 Кружочек '{key}' удалён")
    
    await callback.answer(f"✅ Кружочек удалён")
    await callback.message.edit_text(
        f"🗑 Кружочек для «{name}» удалён",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ К списку кружочков", callback_data="admin_video_notes")]
        ])
    )


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Вернуться в админ-панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    from utils.keyboards import create_admin_keyboard
    
    await callback.answer()
    await callback.message.edit_text(
        "🔐 Админ-панель\n\nВыбери действие:",
        reply_markup=create_admin_keyboard()
    )


