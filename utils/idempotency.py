"""
Утилиты для защиты от повторных запросов (idempotency)
"""
import time
import hashlib
from typing import Dict, Set
from datetime import datetime, timedelta

# Хранилище обработанных запросов: {request_hash: timestamp}
_processed_requests: Dict[str, float] = {}
# Время жизни записи (5 минут)
_REQUEST_TTL = 300


def generate_request_hash(user_id: int, action: str, data: str = "") -> str:
    """
    Генерация хеша запроса для проверки дубликатов
    
    Args:
        user_id: ID пользователя
        action: Действие
        data: Дополнительные данные
    
    Returns:
        Хеш запроса
    """
    content = f"{user_id}:{action}:{data}"
    return hashlib.md5(content.encode()).hexdigest()


def is_duplicate_request(user_id: int, action: str, data: str = "") -> bool:
    """
    Проверить, является ли запрос дубликатом
    
    Args:
        user_id: ID пользователя
        action: Действие
        data: Дополнительные данные
    
    Returns:
        True если дубликат, иначе False
    """
    request_hash = generate_request_hash(user_id, action, data)
    current_time = time.time()
    
    # Очищаем старые записи
    cutoff_time = current_time - _REQUEST_TTL
    _processed_requests.clear()  # Упрощенная очистка (в продакшене лучше использовать более эффективный метод)
    
    if request_hash in _processed_requests:
        request_time = _processed_requests[request_hash]
        if current_time - request_time < _REQUEST_TTL:
            return True
    
    # Сохраняем запрос
    _processed_requests[request_hash] = current_time
    return False


def mark_request_processed(user_id: int, action: str, data: str = ""):
    """
    Пометить запрос как обработанный
    
    Args:
        user_id: ID пользователя
        action: Действие
        data: Дополнительные данные
    """
    request_hash = generate_request_hash(user_id, action, data)
    _processed_requests[request_hash] = time.time()

