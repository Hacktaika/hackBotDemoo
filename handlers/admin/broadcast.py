"""
Рассылка сообщений
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_db_session
from database.models import User, Broadcast
from utils.validators import is_admin
from utils.messages import send_broadcast_message

router = Router()
logger = logging.getLogger(__name__)


class BroadcastStates(StatesGroup):
    """Состояния рассылки"""
    waiting_broadcast = State()


@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Начать рассылку"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(BroadcastStates.waiting_broadcast)
    await callback.message.answer(
        "📢 Отправь сообщение для рассылки в любом формате:\n"
        "• Текст\n"
        "• Фото\n"
        "• Видео\n"
        "• Документ\n"
        "• Аудио\n"
        "• Голосовое сообщение\n"
        "• Видео-кружок\n"
        "• GIF/Анимация\n"
        "• Стикер\n"
        "• Локация\n"
        "• Контакт\n\n"
        "Или отправь /cancel для отмены"
    )


@router.message(BroadcastStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    """Обработка рассылки"""
    admin_id = message.from_user.id
    if not is_admin(admin_id):
        await state.clear()
        return
    
    logger.info(f"📢 Админ {admin_id} начал рассылку")
    
    db = get_db_session()
    try:
        # Получаем всех активных пользователей
        users = db.query(User).filter(User.is_active == True).all()
        logger.info(f"👥 Найдено {len(users)} пользователей для рассылки")
        
        sent_count = 0
        failed_count = 0
        
        # Определяем тип контента и медиа
        content_type = "text"
        text = None
        file_id = None
        media_type = None
        
        # Поддержка всех типов медиа
        if message.photo:
            content_type = "photo"
            file_id = message.photo[-1].file_id
            text = message.caption
        elif message.video:
            content_type = "video"
            file_id = message.video.file_id
            text = message.caption
        elif message.document:
            content_type = "document"
            file_id = message.document.file_id
            text = message.caption
        elif message.audio:
            content_type = "audio"
            file_id = message.audio.file_id
            text = message.caption
        elif message.voice:
            content_type = "voice"
            file_id = message.voice.file_id
            text = message.caption
        elif message.video_note:
            content_type = "video_note"
            file_id = message.video_note.file_id
            text = message.caption
        elif message.animation:
            content_type = "animation"
            file_id = message.animation.file_id
            text = message.caption
        elif message.sticker:
            content_type = "sticker"
            file_id = message.sticker.file_id
            text = message.caption
        elif message.venue:
            content_type = "venue"
            # Для venue используем текст с координатами
            text = f"📍 {message.venue.title}\n{message.venue.address}"
        elif message.location:
            content_type = "location"
            # Для location сохраняем координаты в text
            text = f"{message.location.latitude},{message.location.longitude}"
        elif message.contact:
            content_type = "contact"
            text = f"👤 {message.contact.first_name} {message.contact.phone_number}"
        else:
            # Обычный текст
            text = message.text or message.caption
        
        # Отправляем рассылку
        for user in users:
            try:
                await send_broadcast_message(
                    bot=message.bot,
                    user_id=user.telegram_id,
                    content_type=content_type,
                    text=text,
                    file_id=file_id
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки пользователю {user.telegram_id}: {e}")
                failed_count += 1
        
        # Сохраняем в историю (file_id может быть None для текстовых сообщений)
        broadcast = Broadcast(
            admin_id=admin_id,
            content_type=content_type,
            text=text,
            file_id=file_id,
            sent_count=sent_count,
            failed_count=failed_count
        )
        db.add(broadcast)
        db.commit()
        
        logger.info(f"✅ Рассылка завершена: отправлено {sent_count}, ошибок {failed_count}")
        await message.answer(
            f"✅ Рассылка завершена!\n\n"
            f"Отправлено: {sent_count}\n"
            f"Ошибок: {failed_count}"
        )
        
    finally:
        db.close()
        await state.clear()

