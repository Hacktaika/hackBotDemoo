"""
Статистика и управление пользователями
"""
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_db_session
from database.models import User
from utils.validators import is_admin

router = Router()
logger = logging.getLogger(__name__)


class UserSearchStates(StatesGroup):
    waiting_user_id = State()


def get_stats_keyboard():
    """Клавиатура статистики"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="stats_search_user")],
        [InlineKeyboardButton(text="📋 Список пользователей", callback_data="stats_users_list")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
    ])


def get_user_keyboard(user_id: int):
    """Клавиатура действий с пользователем"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обнулить регистрацию", callback_data=f"user_reset_{user_id}")],
        [InlineKeyboardButton(text="🗑 Удалить пользователя", callback_data=f"user_delete_{user_id}")],
        [InlineKeyboardButton(text="⬅️ К статистике", callback_data="admin_stats")]
    ])


@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    """Показать статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    
    db = get_db_session()
    try:
        # Общая статистика
        total_users = db.query(User).count()
        registered_users = db.query(User).filter(User.is_registered == True).count()
        subscribed_users = db.query(User).filter(User.is_subscribed == True).count()
        
        # За последний месяц
        month_ago = datetime.now() - timedelta(days=30)
        users_this_month = db.query(User).filter(User.created_at >= month_ago).count()
        
        # За сегодня
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        users_today = db.query(User).filter(User.created_at >= today).count()
        
        # За неделю
        week_ago = datetime.now() - timedelta(days=7)
        users_this_week = db.query(User).filter(User.created_at >= week_ago).count()
        
        stats_text = (
            f"📊 <b>Статистика</b>\n\n"
            f"<b>Всего:</b>\n"
            f"👥 Пользователей: {total_users}\n"
            f"✅ Зарегистрировано: {registered_users}\n"
            f"📢 Подписаны на каналы: {subscribed_users}\n\n"
            f"<b>Динамика:</b>\n"
            f"📅 Сегодня: +{users_today}\n"
            f"📆 За неделю: +{users_this_week}\n"
            f"🗓 За месяц: +{users_this_month}"
        )
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_stats_keyboard(),
            parse_mode="HTML"
        )
    finally:
        db.close()


@router.callback_query(F.data == "stats_search_user")
async def start_search_user(callback: CallbackQuery, state: FSMContext):
    """Начать поиск пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(UserSearchStates.waiting_user_id)
    
    await callback.message.edit_text(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Отправь Telegram ID пользователя:\n\n"
        "<i>Для отмены отправь /cancel</i>",
        parse_mode="HTML"
    )


@router.message(UserSearchStates.waiting_user_id)
async def process_user_search(message: Message, state: FSMContext):
    """Обработка поиска пользователя"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи корректный ID (число)")
        return
    
    await state.clear()
    
    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await message.answer(
                f"❌ Пользователь с ID {user_id} не найден",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ К статистике", callback_data="admin_stats")]
                ])
            )
            return
        
        await message.answer(
            format_user_info(user),
            reply_markup=get_user_keyboard(user.telegram_id),
            parse_mode="HTML"
        )
    finally:
        db.close()


def get_users_list_keyboard(page: int, total_pages: int):
    """Клавиатура для списка пользователей с пагинацией"""
    buttons = []
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"users_page_{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"users_page_{page + 1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="stats_search_user")])
    buttons.append([InlineKeyboardButton(text="⬅️ К статистике", callback_data="admin_stats")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "stats_users_list")
async def show_users_list(callback: CallbackQuery):
    """Показать список пользователей (первая страница)"""
    await show_users_page(callback, 0)


@router.callback_query(F.data.startswith("users_page_"))
async def show_users_page_handler(callback: CallbackQuery):
    """Показать конкретную страницу пользователей"""
    page = int(callback.data.replace("users_page_", ""))
    await show_users_page(callback, page)


async def show_users_page(callback: CallbackQuery, page: int):
    """Показать страницу пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    
    per_page = 20
    offset = page * per_page
    
    db = get_db_session()
    try:
        total_users = db.query(User).count()
        total_pages = (total_users + per_page - 1) // per_page  # Округление вверх
        
        if total_users == 0:
            await callback.message.edit_text(
                "📋 Пользователей пока нет",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ К статистике", callback_data="admin_stats")]
                ])
            )
            return
        
        users = db.query(User).order_by(User.created_at.desc()).offset(offset).limit(per_page).all()
        
        text = f"📋 <b>Пользователи</b> (стр. {page + 1}/{total_pages})\n"
        text += f"<i>Всего: {total_users}</i>\n\n"
        
        for user in users:
            status = "✅" if user.is_registered else "❌"
            name = user.name or user.first_name or "Без имени"
            date = user.created_at.strftime("%d.%m.%Y") if user.created_at else "?"
            text += f"{status} <code>{user.telegram_id}</code> — {name} ({date})\n"
        
        text += "\n<i>Нажми на ID чтобы скопировать</i>"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_users_list_keyboard(page, total_pages),
            parse_mode="HTML"
        )
    finally:
        db.close()


@router.callback_query(F.data.startswith("user_reset_"))
async def reset_user(callback: CallbackQuery):
    """Обнулить пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    user_id = int(callback.data.replace("user_reset_", ""))
    
    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Обнуляем данные
        user.is_registered = False
        user.is_subscribed = False
        user.name = None
        user.position = None
        user.expectations = None
        user.source = None
        user.quiz_completed = False
        user.gift_received = False
        
        db.commit()
        logger.info(f"🔄 Пользователь {user_id} обнулён админом {callback.from_user.id}")
        
        await callback.answer("✅ Пользователь обнулён!")
        await callback.message.edit_text(
            f"✅ <b>Пользователь обнулён</b>\n\n"
            f"ID: <code>{user_id}</code>\n\n"
            f"Теперь при /start ему снова покажется опрос.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ К статистике", callback_data="admin_stats")]
            ]),
            parse_mode="HTML"
        )
    finally:
        db.close()


@router.callback_query(F.data.startswith("user_delete_"))
async def delete_user(callback: CallbackQuery):
    """Удалить пользователя полностью"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    user_id = int(callback.data.replace("user_delete_", ""))
    
    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Удаляем пользователя
        db.delete(user)
        db.commit()
        logger.info(f"🗑 Пользователь {user_id} удалён админом {callback.from_user.id}")
        
        await callback.answer("✅ Пользователь удалён!")
        await callback.message.edit_text(
            f"🗑 <b>Пользователь удалён</b>\n\n"
            f"ID: <code>{user_id}</code>\n\n"
            f"Все данные удалены из базы.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ К статистике", callback_data="admin_stats")]
            ]),
            parse_mode="HTML"
        )
    finally:
        db.close()


def format_user_info(user: User) -> str:
    """Форматировать информацию о пользователе"""
    status_reg = "✅ Да" if user.is_registered else "❌ Нет"
    status_sub = "✅ Да" if user.is_subscribed else "❌ Нет"
    status_bonus = "✅ Да" if user.has_bonus else "❌ Нет"
    status_active = "✅ Активен" if user.is_active else "❌ Неактивен"
    
    created = user.created_at.strftime("%d.%m.%Y %H:%M") if user.created_at else "Неизвестно"
    updated = user.updated_at.strftime("%d.%m.%Y %H:%M") if user.updated_at else "Неизвестно"
    
    return (
        f"👤 <b>Пользователь</b>\n\n"
        f"<b>Telegram:</b>\n"
        f"• ID: <code>{user.telegram_id}</code>\n"
        f"• Username: @{user.username or 'нет'}\n"
        f"• Имя TG: {user.first_name or 'нет'} {user.last_name or ''}\n\n"
        f"<b>Анкета:</b>\n"
        f"• Имя: {user.name or 'не указано'}\n"
        f"• Должность: {user.position or 'не указана'}\n"
        f"• Ожидания: {user.expectations or 'не указаны'}\n"
        f"• Источник: {user.source or 'не указан'}\n\n"
        f"<b>Статусы:</b>\n"
        f"• Зарегистрирован: {status_reg}\n"
        f"• Подписан на каналы: {status_sub}\n"
        f"• Получил бонус: {status_bonus}\n"
        f"• Статус: {status_active}\n\n"
        f"<b>Даты:</b>\n"
        f"• Первый визит: {created}\n"
        f"• Последняя активность: {updated}"
    )
