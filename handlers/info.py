"""
Обработчик информационных страниц
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import settings

router = Router()

# File ID фоток
HACKTAIKA_PHOTO = "AgACAgIAAxkBAAO3aUL3VRFwOpoELxZIqWWODyJVS4IAAgMNaxsTtRlK8k2l1SHtYE8BAAMCAAN5AAM2BA"
DISLOV_PHOTO = "AgACAgIAAxkBAAO5aUL3orA8RBU6oxme_5QHhQqLwIYAAggNaxsTtRlKJPq84PGjox8BAAMCAAN4AAM2BA"

HACKTAIKA_TEXT = """🦅 <b>Хактайка — это</b>

Мы молодое IT-агентство, которое <b>не боится смелых решений</b>. Живя и развиваясь не в самые простые времена нашей страны, мы готовы делать громкие и сильные заявления в сфере IT.

У нас много планов на этот рынок. Оставайтесь с нами, смотрите и повышайте свои знания по разработке и бизнесу в наших соцсетях. Уверен, наш контент вам понравится.

💡 <b>У нас есть миссия, которую мы выполняем.</b>

Нам очень важно сделать так, чтобы вам было понятно:
• Что делается в вашем проекте?
• Как это работает?
• За что мы заплатили?"""

DISLOV_TEXT = """👨‍💻 <b>Дислов — это</b>

Парень из нового поколения, который занимается разными видами деятельности в интернете и пытается на этом зарабатывать.

На своём канале он показывает:
• Как построить бизнес
• В чём сложности
• Почему всё получается именно так

🎯 <b>Ответы — на канале!</b>"""

# Ссылки на каналы
DISLOV_CHANNEL = "https://t.me/+dIPhAIKR1YsxYzky"
HACKTAIKA_CHANNEL = "https://t.me/+vO3KPLB0HyYwYTNi"


def get_info_keyboard(info_type: str):
    """Клавиатура для инфо-страницы"""
    buttons = []
    
    if info_type == "hacktaika":
        buttons.append([InlineKeyboardButton(text="📢 Канал ХакТайки", url=HACKTAIKA_CHANNEL)])
        buttons.append([InlineKeyboardButton(text="🌐 Перейти на сайт", url=settings.SITE_URL)])
    elif info_type == "founder":
        buttons.append([InlineKeyboardButton(text="📢 Канал Дислова", url=DISLOV_CHANNEL)])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Вернуться", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("info_"))
async def show_info(callback: CallbackQuery):
    """Показать информационную страницу"""
    await callback.answer()
    
    info_type = callback.data.split("_")[1]  # hacktaika или founder
    
    if info_type == "hacktaika":
        text = HACKTAIKA_TEXT
        photo = HACKTAIKA_PHOTO
    elif info_type == "founder":
        text = DISLOV_TEXT
        photo = DISLOV_PHOTO
    else:
        await callback.message.answer("❌ Страница не найдена")
        return
    
    keyboard = get_info_keyboard(info_type)
    
    # Удаляем старое сообщение и отправляем новое
    try:
        await callback.message.delete()
    except:
        pass
    
    if photo:
        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML",
            has_spoiler=True  # Спойлер для фото
        )
    else:
        await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
