"""
Утилиты для отправки сообщений
"""
from typing import Optional
from aiogram.types import Message, CallbackQuery
from database.models import Content


async def send_content(message: Message, content: Content):
    """
    Отправить контент пользователю (с поддержкой HTML-форматирования)
    
    Args:
        message: Сообщение для ответа
        content: Объект контента из БД
    """
    if content.content_type == "text":
        await message.answer(content.text or "", parse_mode="HTML")
    elif content.content_type == "photo":
        await message.answer_photo(
            photo=content.file_id,
            caption=content.text,
            parse_mode="HTML"
        )
    elif content.content_type == "video":
        await message.answer_video(
            video=content.file_id,
            caption=content.text,
            parse_mode="HTML"
        )
    elif content.content_type == "document":
        await message.answer_document(
            document=content.file_id,
            caption=content.text,
            parse_mode="HTML"
        )


async def send_broadcast_message(bot, user_id: int, content_type: str, text: Optional[str], file_id: Optional[str]):
    """
    Отправить сообщение рассылки пользователю (с поддержкой HTML)
    """
    if content_type == "text":
        await bot.send_message(chat_id=user_id, text=text or "📢 Рассылка", parse_mode="HTML")
    elif content_type == "photo":
        await bot.send_photo(chat_id=user_id, photo=file_id, caption=text, parse_mode="HTML")
    elif content_type == "video":
        await bot.send_video(chat_id=user_id, video=file_id, caption=text, parse_mode="HTML")
    elif content_type == "document":
        await bot.send_document(chat_id=user_id, document=file_id, caption=text, parse_mode="HTML")
    elif content_type == "audio":
        await bot.send_audio(chat_id=user_id, audio=file_id, caption=text, parse_mode="HTML")
    elif content_type == "voice":
        await bot.send_voice(chat_id=user_id, voice=file_id, caption=text, parse_mode="HTML")
    elif content_type == "video_note":
        await bot.send_video_note(chat_id=user_id, video_note=file_id)
        if text:
            await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
    elif content_type == "animation":
        await bot.send_animation(chat_id=user_id, animation=file_id, caption=text, parse_mode="HTML")
    elif content_type == "sticker":
        await bot.send_sticker(chat_id=user_id, sticker=file_id)
        if text:
            await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
    else:
        await bot.send_message(chat_id=user_id, text=text or "📢 Рассылка", parse_mode="HTML")
