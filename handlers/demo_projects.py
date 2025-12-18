"""
Обработчик каталога демо проектов
"""
from typing import Union
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from sqlalchemy.orm import Session
from database.models import DemoProject
from database.db import get_db_session
from config import settings

router = Router()


def create_demo_keyboard(project: DemoProject, current_index: int, total_count: int) -> InlineKeyboardMarkup:
    """
    Создать клавиатуру для демо проекта
    
    Args:
        project: Текущий проект
        current_index: Индекс текущего проекта (0-based)
        total_count: Общее количество проектов
    """
    from config import DEFAULT_DEMO_APP_URL
    
    buttons = []
    
    # Кнопка "Перейти на приложение" - первая строка
    app_url = project.app_url or DEFAULT_DEMO_APP_URL
    if app_url:
        buttons.append([InlineKeyboardButton(text="🚀 Приложение", url=app_url)])
    
    # Кнопки навигации "Назад" и "Дальше" - вторая строка
    nav_row = []
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"demo_prev_{current_index}"))
    if current_index < total_count - 1:
        nav_row.append(InlineKeyboardButton(text="➡️ Дальше", callback_data=f"demo_next_{current_index}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    # Кнопка "На канал" - третья строка
    channel_url = project.channel_url
    if not channel_url and settings.CHANNEL1_USERNAME:
        channel_url = f"https://t.me/{settings.CHANNEL1_USERNAME.replace('@', '')}"
    
    if channel_url:
        buttons.append([InlineKeyboardButton(text="📢 На канал", url=channel_url)])
    
    # Кнопка "Вернуться в меню" - последняя строка
    buttons.append([InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def show_demo_project(callback_or_message: Union[CallbackQuery, Message], project_index: int = 0):
    """
    Показать демо проект
    
    Args:
        callback_or_message: CallbackQuery или Message
        project_index: Индекс проекта для отображения
    """
    db = get_db_session()
    try:
        # Получаем все активные проекты, отсортированные по order_index
        projects = db.query(DemoProject).filter(
            DemoProject.is_active == True
        ).order_by(DemoProject.order_index.asc()).all()
        
        if not projects:
            text = "📦 Каталог демо проектов пуст.\n\nСкоро здесь появятся интересные проекты!"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="menu_main")]
            ])
            
            if isinstance(callback_or_message, CallbackQuery):
                try:
                    await callback_or_message.message.delete()
                except:
                    pass
                await callback_or_message.message.answer(text, reply_markup=keyboard)
            else:
                await callback_or_message.answer(text, reply_markup=keyboard)
            return
        
        # Проверяем индекс
        if project_index < 0:
            project_index = 0
        if project_index >= len(projects):
            project_index = len(projects) - 1
        
        project = projects[project_index]
        
        # Формируем описание - используем HTML форматирование
        description = project.description or "Описание проекта"
        
        # Создаем клавиатуру
        keyboard = create_demo_keyboard(project, project_index, len(projects))
        
        # Отправляем проект
        if isinstance(callback_or_message, CallbackQuery):
            try:
                await callback_or_message.message.delete()
            except:
                pass
            
            if project.photo_file_id:
                await callback_or_message.message.answer_photo(
                    photo=project.photo_file_id,
                    caption=description,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await callback_or_message.message.answer(
                    description,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        else:
            if project.photo_file_id:
                await callback_or_message.answer_photo(
                    photo=project.photo_file_id,
                    caption=description,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await callback_or_message.answer(
                    description,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
    finally:
        db.close()


@router.callback_query(F.data == "demo_projects")
async def show_demo_projects_menu(callback: CallbackQuery):
    """Показать каталог демо проектов (первый проект)"""
    await callback.answer()
    await show_demo_project(callback, project_index=0)


@router.callback_query(F.data.startswith("demo_next_"))
async def show_next_demo(callback: CallbackQuery):
    """Показать следующий проект"""
    await callback.answer()
    try:
        project_index = int(callback.data.split("_")[-1]) + 1
        await show_demo_project(callback, project_index=project_index)
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка навигации", show_alert=True)


@router.callback_query(F.data.startswith("demo_prev_"))
async def show_prev_demo(callback: CallbackQuery):
    """Показать предыдущий проект"""
    await callback.answer()
    try:
        project_index = int(callback.data.split("_")[-1]) - 1
        await show_demo_project(callback, project_index=project_index)
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка навигации", show_alert=True)

