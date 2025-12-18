"""
Управление демо проектами
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import get_db_session
from database.models import DemoProject
from utils.validators import is_admin, validate_message_size
from utils.rate_limit import check_admin_rate_limit

router = Router()
logger = logging.getLogger(__name__)


class DemoProjectStates(StatesGroup):
    """Состояния управления демо проектами"""
    waiting_action = State()
    waiting_title = State()
    waiting_description = State()
    waiting_photo = State()
    waiting_app_url = State()
    waiting_channel_url = State()
    waiting_order = State()
    waiting_edit_project_id = State()
    waiting_edit_field = State()


@router.callback_query(F.data == "admin_demo_projects")
async def demo_projects_menu(callback: CallbackQuery):
    """Меню управления демо проектами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    
    db = get_db_session()
    try:
        projects = db.query(DemoProject).filter(DemoProject.is_active == True).order_by(DemoProject.order_index.asc()).all()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить проект", callback_data="admin_demo_add")],
            [InlineKeyboardButton(text="📋 Список проектов", callback_data="admin_demo_list")],
            [InlineKeyboardButton(text="✏️ Редактировать проект", callback_data="admin_demo_edit")],
            [InlineKeyboardButton(text="🗑️ Удалить проект", callback_data="admin_demo_delete")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ])
        
        text = (
            f"📦 <b>Управление демо проектами</b>\n\n"
            f"Всего активных проектов: {len(projects)}\n\n"
            f"Выбери действие:"
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    finally:
        db.close()


@router.callback_query(F.data == "admin_demo_list")
async def list_demo_projects(callback: CallbackQuery):
    """Список всех демо проектов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    
    db = get_db_session()
    try:
        projects = db.query(DemoProject).order_by(DemoProject.order_index.asc()).all()
        
        if not projects:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_demo_projects")]
            ])
            await callback.message.edit_text(
                "📦 Список проектов пуст",
                reply_markup=keyboard
            )
            return
        
        text = "📦 <b>Список демо проектов:</b>\n\n"
        for i, project in enumerate(projects, 1):
            status = "✅" if project.is_active else "❌"
            text += (
                f"{i}. {status} <b>{project.title}</b>\n"
                f"   Порядок: {project.order_index}\n"
                f"   ID: {project.id}\n\n"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_demo_projects")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    finally:
        db.close()


@router.callback_query(F.data == "admin_demo_add")
async def add_demo_project_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление демо проекта"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(DemoProjectStates.waiting_title)
    await callback.message.edit_text("➕ <b>Добавление демо проекта</b>\n\nВведи название проекта:", parse_mode="HTML")


@router.message(DemoProjectStates.waiting_title)
async def process_demo_title(message: Message, state: FSMContext):
    """Обработка названия проекта"""
    if not validate_message_size(message) or not message.text:
        await message.answer("❌ Некорректное название. Попробуй еще раз.")
        return
    
    title = message.text.strip()[:255]
    await state.update_data(title=title)
    await state.set_state(DemoProjectStates.waiting_description)
    await message.answer("📝 Введи описание проекта (HTML форматирование):")


@router.message(DemoProjectStates.waiting_description)
async def process_demo_description(message: Message, state: FSMContext):
    """Обработка описания проекта"""
    if not validate_message_size(message) or not message.text:
        await message.answer("❌ Некорректное описание. Попробуй еще раз.")
        return
    
    description = message.text.strip()[:4096]
    await state.update_data(description=description)
    await state.set_state(DemoProjectStates.waiting_photo)
    await message.answer("📷 Отправь фото проекта (или /skip чтобы пропустить):")


@router.message(DemoProjectStates.waiting_photo)
async def process_demo_photo(message: Message, state: FSMContext):
    """Обработка фото проекта"""
    photo_file_id = None
    
    if message.text and message.text.strip() == "/skip":
        pass
    elif message.photo:
        photo_file_id = message.photo[-1].file_id
    else:
        await message.answer("❌ Отправь фото или /skip")
        return
    
    await state.update_data(photo_file_id=photo_file_id)
    await state.set_state(DemoProjectStates.waiting_app_url)
    await message.answer("🔗 Введи ссылку на приложение (или /skip):")


@router.message(DemoProjectStates.waiting_app_url)
async def process_demo_app_url(message: Message, state: FSMContext):
    """Обработка ссылки на приложение"""
    app_url = None
    
    if message.text and message.text.strip() != "/skip":
        app_url = message.text.strip()[:500]
    
    await state.update_data(app_url=app_url)
    await state.set_state(DemoProjectStates.waiting_channel_url)
    await message.answer("📢 Введи ссылку на канал (или /skip):")


@router.message(DemoProjectStates.waiting_channel_url)
async def process_demo_channel_url(message: Message, state: FSMContext):
    """Обработка ссылки на канал"""
    channel_url = None
    
    if message.text and message.text.strip() != "/skip":
        channel_url = message.text.strip()[:500]
    
    await state.update_data(channel_url=channel_url)
    await state.set_state(DemoProjectStates.waiting_order)
    await message.answer("🔢 Введи порядковый номер (0, 1, 2...):")


@router.message(DemoProjectStates.waiting_order)
async def process_demo_order(message: Message, state: FSMContext):
    """Обработка порядка проекта"""
    try:
        order_index = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи число. Попробуй еще раз:")
        return
    
    data = await state.get_data()
    
    db = get_db_session()
    try:
        project = DemoProject(
            title=data['title'],
            description=data['description'],
            photo_file_id=data.get('photo_file_id'),
            app_url=data.get('app_url'),
            channel_url=data.get('channel_url'),
            order_index=order_index,
            is_active=True
        )
        db.add(project)
        db.commit()
        
        await message.answer(f"✅ Проект '{data['title']}' успешно добавлен!")
        logger.info(f"✅ Админ {message.from_user.id} добавил проект: {data['title']}")
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении проекта: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при добавлении проекта.")
    finally:
        db.close()
        await state.clear()


@router.callback_query(F.data == "admin_demo_edit")
async def edit_demo_project_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование проекта"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(DemoProjectStates.waiting_edit_project_id)
    await callback.message.edit_text("✏️ <b>Редактирование проекта</b>\n\nВведи ID проекта для редактирования:", parse_mode="HTML")


@router.message(DemoProjectStates.waiting_edit_project_id)
async def process_edit_project_id(message: Message, state: FSMContext):
    """Обработка ID проекта для редактирования/удаления"""
    data = await state.get_data()
    action = data.get('action')
    
    try:
        project_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи число (ID проекта). Попробуй еще раз:")
        return
    
    db = get_db_session()
    try:
        project = db.query(DemoProject).filter(DemoProject.id == project_id).first()
        
        if not project:
            await message.answer("❌ Проект с таким ID не найден.")
            await state.clear()
            return
        
        # Если это удаление
        if action == "delete":
            project.is_active = False
            db.commit()
            await message.answer(f"✅ Проект '{project.title}' деактивирован (удален).")
            logger.info(f"✅ Админ {message.from_user.id} удалил проект {project_id}")
            await state.clear()
            return
        
        # Если это редактирование
        await state.update_data(project_id=project_id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data="edit_field_title")],
            [InlineKeyboardButton(text="📄 Описание", callback_data="edit_field_description")],
            [InlineKeyboardButton(text="📷 Фото", callback_data="edit_field_photo")],
            [InlineKeyboardButton(text="🔗 Ссылка на приложение", callback_data="edit_field_app_url")],
            [InlineKeyboardButton(text="📢 Ссылка на канал", callback_data="edit_field_channel_url")],
            [InlineKeyboardButton(text="🔢 Порядок", callback_data="edit_field_order")],
            [InlineKeyboardButton(text="✅/❌ Активность", callback_data="edit_field_active")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_demo_projects")]
        ])
        
        status = "✅ Активен" if project.is_active else "❌ Неактивен"
        await message.answer(
            f"✏️ <b>Редактирование проекта:</b>\n\n"
            f"ID: {project.id}\n"
            f"Название: {project.title}\n"
            f"Порядок: {project.order_index}\n"
            f"Статус: {status}\n\n"
            f"Что хочешь изменить?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    finally:
        db.close()


@router.callback_query(F.data.startswith("edit_field_"))
async def edit_field_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование поля"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    field = callback.data.replace("edit_field_", "")
    await callback.answer()
    
    data = await state.get_data()
    project_id = data.get('project_id')
    
    if not project_id:
        await callback.message.answer("❌ Ошибка. Начни заново.")
        await state.clear()
        return
    
    db = get_db_session()
    try:
        project = db.query(DemoProject).filter(DemoProject.id == project_id).first()
        
        if not project:
            await callback.message.answer("❌ Проект не найден.")
            await state.clear()
            return
        
        await state.update_data(edit_field=field)
        
        field_names = {
            "title": "название",
            "description": "описание",
            "photo": "фото",
            "app_url": "ссылку на приложение",
            "channel_url": "ссылку на канал",
            "order": "порядок",
            "active": "активность"
        }
        
        if field == "active":
            # Переключаем активность сразу
            project.is_active = not project.is_active
            db.commit()
            await callback.message.answer(f"✅ Активность проекта изменена на: {'Активен' if project.is_active else 'Неактивен'}")
            await state.clear()
        elif field == "photo":
            await state.set_state(DemoProjectStates.waiting_edit_field)
            await callback.message.answer("📷 Отправь новое фото (или /skip чтобы удалить):")
        elif field == "order":
            await state.set_state(DemoProjectStates.waiting_edit_field)
            await callback.message.answer(f"🔢 Текущий порядок: {project.order_index}\nВведи новый порядок:")
        else:
            await state.set_state(DemoProjectStates.waiting_edit_field)
            current_value = getattr(project, field, "")
            await callback.message.answer(f"✏️ Текущее значение: {current_value or '(пусто)'}\nВведи новое {field_names.get(field, field)}:")
    finally:
        db.close()


@router.message(DemoProjectStates.waiting_edit_field)
async def process_edit_field(message: Message, state: FSMContext):
    """Обработка нового значения поля"""
    data = await state.get_data()
    project_id = data.get('project_id')
    field = data.get('edit_field')
    
    if not project_id or not field:
        await message.answer("❌ Ошибка. Начни заново.")
        await state.clear()
        return
    
    db = get_db_session()
    try:
        project = db.query(DemoProject).filter(DemoProject.id == project_id).first()
        
        if not project:
            await message.answer("❌ Проект не найден.")
            await state.clear()
            return
        
        if field == "photo":
            if message.text and message.text.strip() == "/skip":
                project.photo_file_id = None
            elif message.photo:
                project.photo_file_id = message.photo[-1].file_id
            else:
                await message.answer("❌ Отправь фото или /skip")
                return
        elif field == "order":
            try:
                project.order_index = int(message.text.strip())
            except ValueError:
                await message.answer("❌ Введи число. Попробуй еще раз:")
                return
        elif field == "title":
            project.title = message.text.strip()[:255]
        elif field == "description":
            project.description = message.text.strip()[:4096]
        elif field == "app_url":
            if message.text.strip() == "/skip":
                project.app_url = None
            else:
                project.app_url = message.text.strip()[:500]
        elif field == "channel_url":
            if message.text.strip() == "/skip":
                project.channel_url = None
            else:
                project.channel_url = message.text.strip()[:500]
        
        db.commit()
        await message.answer(f"✅ Поле '{field}' успешно обновлено!")
        logger.info(f"✅ Админ {message.from_user.id} обновил поле {field} проекта {project_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении проекта: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при обновлении.")
    finally:
        db.close()
        await state.clear()


@router.callback_query(F.data == "admin_demo_delete")
async def delete_demo_project_start(callback: CallbackQuery, state: FSMContext):
    """Начать удаление проекта"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(DemoProjectStates.waiting_edit_project_id)
    await state.update_data(action="delete")  # Сохраняем действие
    await callback.message.edit_text("🗑️ <b>Удаление проекта</b>\n\nВведи ID проекта для удаления:", parse_mode="HTML")


@router.callback_query(F.data == "admin_back")
async def back_to_admin_menu(callback: CallbackQuery):
    """Вернуться в админ-меню"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    from utils.keyboards import create_admin_keyboard
    
    await callback.answer()
    keyboard = create_admin_keyboard()
    await callback.message.edit_text(
        "🔐 Админ-панель\n\nВыбери действие:",
        reply_markup=keyboard
    )

