"""
Обработчик раздачи PDF файла
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.db import get_db_session
from database.models import User
from handlers.menu import show_main_menu

router = Router()
logger = logging.getLogger(__name__)

# File ID PDF файла (нужно будет получить, отправив файл боту)
# После отправки PDF боту (как админ), получите file_id и укажите его здесь
PDF_FILE_ID = None  # Замените на file_id после отправки PDF боту


@router.callback_query(F.data == "get_pdf")
async def send_pdf(callback: CallbackQuery):
    """Отправить PDF файл пользователю (только один раз)"""
    await callback.answer()
    
    user_id = callback.from_user.id
    db = get_db_session()
    
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            await callback.message.answer("❌ Пользователь не найден. Используй /start")
            return
        
        # Проверяем, не получил ли уже PDF
        if user.has_pdf:
            logger.info(f"⚠️ Пользователь {user_id} уже получил PDF")
            await callback.message.answer("✅ Вы уже получили PDF файл ранее.")
            return
        
        # Проверяем наличие file_id
        if not PDF_FILE_ID:
            logger.error("❌ PDF_FILE_ID не установлен в config")
            await callback.message.answer(
                "❌ PDF файл временно недоступен. Обратитесь к администратору."
            )
            return
        
        # Отправляем PDF
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer_document(
            document=PDF_FILE_ID,
            caption=(
                "📄 <b>Скрытые ловушки в IT-разработке, о которых молчат 90% агентств</b>\n\n"
                "Практический гид по управлению IT-проектами и минимизации рисков.\n\n"
                "Спасибо за интерес!"
            ),
            parse_mode="HTML"
        )
        
        # Отмечаем, что пользователь получил PDF
        user.has_pdf = True
        db.commit()
        
        logger.info(f"✅ Пользователь {user_id} получил PDF файл")
        
        # Обновляем меню (кнопка PDF исчезнет)
        await show_main_menu(callback.message, db, user, edit=False)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке PDF пользователю {user_id}: {e}", exc_info=True)
        await callback.message.answer("❌ Произошла ошибка при отправке PDF. Попробуйте позже.")
    finally:
        db.close()

