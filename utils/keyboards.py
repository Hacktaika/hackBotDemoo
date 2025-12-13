"""
Утилиты для создания клавиатур
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import settings


def create_subscription_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру для подписки на каналы"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Канал 1", url=f"https://t.me/{settings.CHANNEL1_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton(text="📢 Канал 2", url=f"https://t.me/{settings.CHANNEL2_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")]
    ])


def create_back_button(callback_data: str = "menu_main") -> InlineKeyboardMarkup:
    """Создать клавиатуру с кнопкой "Назад" """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Вернуться", callback_data=callback_data)]
    ])


def create_info_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру для информационных страниц"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Перейти на сайт", url=settings.SITE_URL)],
        [InlineKeyboardButton(text="⬅️ Вернуться", callback_data="menu_main")]
    ])


def create_admin_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру админ-панели"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="➕ Добавить контент", callback_data="admin_add_content")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")]
    ])


def create_source_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора источника"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Соцсети", callback_data="source_social")],
        [InlineKeyboardButton(text="📢 Сарафанка", callback_data="source_word_of_mouth")],
        [InlineKeyboardButton(text="🌐 На сайте", callback_data="source_website")],
        [InlineKeyboardButton(text="🔗 Другие источники", callback_data="source_other")]
    ])

