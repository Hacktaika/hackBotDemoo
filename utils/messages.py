"""
Утилиты для отправки сообщений
"""
from typing import Optional
from aiogram.types import Message, CallbackQuery
from database.models import Content, Gift


async def send_content(message: Message, content: Content):
    """
    Отправить контент пользователю
    
    Args:
        message: Сообщение для ответа
        content: Объект контента из БД
    """
    if content.content_type == "text":
        await message.answer(content.text or "")
    elif content.content_type == "photo":
        await message.answer_photo(
            photo=content.file_id,
            caption=content.text
        )
    elif content.content_type == "video":
        await message.answer_video(
            video=content.file_id,
            caption=content.text
        )
    elif content.content_type == "document":
        await message.answer_document(
            document=content.file_id,
            caption=content.text
        )


async def send_gift(callback: CallbackQuery, gift: Gift, text: str, keyboard):
    """
    Отправить подарок пользователю
    
    Args:
        callback: CallbackQuery для ответа
        gift: Объект подарка из БД
        text: Текст для отправки
        keyboard: Клавиатура
    """
    if gift.file_id:
        if gift.content_type == "photo":
            await callback.message.answer_photo(
                photo=gift.file_id,
                caption=text,
                reply_markup=keyboard
            )
        elif gift.content_type == "video":
            await callback.message.answer_video(
                video=gift.file_id,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.answer_document(
                document=gift.file_id,
                caption=text,
                reply_markup=keyboard
            )
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)


async def send_broadcast_message(bot, user_id: int, content_type: str, text: Optional[str], file_id: Optional[str]):
    """
    Отправить сообщение рассылки пользователю
    
    Поддерживает все типы медиа: text, photo, video, document, audio, voice, 
    video_note, animation, sticker, venue, location, contact
    
    Args:
        bot: Экземпляр бота
        user_id: ID пользователя
        content_type: Тип контента
        text: Текст сообщения или caption
        file_id: ID файла в Telegram (может быть None для текста)
    """
    if content_type == "text":
        await bot.send_message(chat_id=user_id, text=text or "📢 Рассылка")
    elif content_type == "photo":
        await bot.send_photo(chat_id=user_id, photo=file_id, caption=text)
    elif content_type == "video":
        await bot.send_video(chat_id=user_id, video=file_id, caption=text)
    elif content_type == "document":
        await bot.send_document(chat_id=user_id, document=file_id, caption=text)
    elif content_type == "audio":
        await bot.send_audio(chat_id=user_id, audio=file_id, caption=text)
    elif content_type == "voice":
        await bot.send_voice(chat_id=user_id, voice=file_id, caption=text)
    elif content_type == "video_note":
        await bot.send_video_note(chat_id=user_id, video_note=file_id)
        if text:
            await bot.send_message(chat_id=user_id, text=text)
    elif content_type == "animation":
        await bot.send_animation(chat_id=user_id, animation=file_id, caption=text)
    elif content_type == "sticker":
        await bot.send_sticker(chat_id=user_id, sticker=file_id)
        if text:
            await bot.send_message(chat_id=user_id, text=text)
    elif content_type == "venue":
        # Для venue нужно парсить координаты из text
        if text:
            await bot.send_message(chat_id=user_id, text=text)
    elif content_type == "location":
        # Для location парсим координаты из text
        if text and "," in text:
            try:
                lat, lon = map(float, text.split(","))
                await bot.send_location(chat_id=user_id, latitude=lat, longitude=lon)
            except ValueError:
                await bot.send_message(chat_id=user_id, text=text)
        else:
            await bot.send_message(chat_id=user_id, text=text or "📍 Локация")
    elif content_type == "contact":
        if text:
            await bot.send_message(chat_id=user_id, text=text)
    else:
        # Fallback для неизвестных типов
        await bot.send_message(chat_id=user_id, text=text or "📢 Рассылка")

