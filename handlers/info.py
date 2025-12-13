"""
Обработчик информационных страниц
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.db import get_db_session
from database.models import InfoPage
from utils.keyboards import create_info_keyboard

router = Router()


@router.callback_query(F.data.startswith("info_"))
async def show_info(callback: CallbackQuery):
    """Показать информационную страницу"""
    await callback.answer()
    
    info_type = callback.data.split("_")[1]  # hacktaika или founder
    slug_map = {
        "hacktaika": "hacktaika",
        "founder": "founder"
    }
    slug = slug_map.get(info_type)
    
    if not slug:
        await callback.message.answer("❌ Страница не найдена")
        return
    
    db = get_db_session()
    try:
        page = db.query(InfoPage).filter(InfoPage.slug == slug).first()
        
        if not page:
            # Заглушка если страница не создана
            if slug == "hacktaika":
                text = (
                    "ℹ️ ХакТайка\n\n"
                    "Здесь будет информация о ХакТайке.\n"
                    "Что это такое, кто мы и чем занимаемся."
                )
            else:
                text = (
                    "👤 Основатель\n\n"
                    "Здесь будет информация об основателе проекта."
                )
        else:
            text = f"{page.title}\n\n{page.text}"
        
        keyboard = create_info_keyboard()
        
        if page and page.photo_file_id:
            await callback.message.answer_photo(
                photo=page.photo_file_id,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(text, reply_markup=keyboard)
            
    finally:
        db.close()

