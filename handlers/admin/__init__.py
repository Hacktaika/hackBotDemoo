"""
Админ-панель
"""
from aiogram import Router
from .broadcast import router as broadcast_router
from .content import router as content_router
from .stats import router as stats_router
from .main import router as main_router
from .video_notes import router as video_notes_router

router = Router()
router.include_router(main_router)
router.include_router(broadcast_router)
router.include_router(content_router)
router.include_router(stats_router)
router.include_router(video_notes_router)




