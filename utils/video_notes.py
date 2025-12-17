"""
Управление кружочками опроса
"""
import json
import os
from typing import Optional

VIDEO_NOTES_FILE = "./data/video_notes.json"

# Названия кружочков
VIDEO_NOTE_KEYS = {
    "name": "Вопрос 1: Как тебя зовут?",
    "position": "Вопрос 2: Какая должность?",
    "expectations": "Вопрос 3: Что хочешь получить?",
    "source": "Вопрос 4: Как узнал о боте?",
    "finish": "Завершение опроса"
}


def _ensure_file():
    """Создать файл если не существует"""
    os.makedirs(os.path.dirname(VIDEO_NOTES_FILE), exist_ok=True)
    if not os.path.exists(VIDEO_NOTES_FILE):
        with open(VIDEO_NOTES_FILE, 'w') as f:
            json.dump({}, f)


def get_video_notes() -> dict:
    """Получить все кружочки"""
    _ensure_file()
    try:
        with open(VIDEO_NOTES_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def get_video_note(key: str) -> Optional[str]:
    """Получить file_id кружочка по ключу"""
    notes = get_video_notes()
    return notes.get(key)


def set_video_note(key: str, file_id: str):
    """Установить file_id кружочка"""
    notes = get_video_notes()
    notes[key] = file_id
    with open(VIDEO_NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=2)


def delete_video_note(key: str):
    """Удалить кружочек"""
    notes = get_video_notes()
    if key in notes:
        del notes[key]
        with open(VIDEO_NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=2)
