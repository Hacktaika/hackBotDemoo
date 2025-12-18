"""
Утилиты для защиты от спама и DDoS
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter для защиты от спама"""
    
    def __init__(self):
        # Хранилище запросов: {user_id: [(timestamp, action), ...]}
        self._requests: Dict[int, list] = defaultdict(list)
        # Блокированные пользователи: {user_id: unblock_timestamp}
        self._blocked: Dict[int, float] = {}
        # Статистика нарушений
        self._violations: Dict[int, int] = defaultdict(int)
    
    def check_rate_limit(
        self,
        user_id: int,
        max_requests: int = 10,
        time_window: int = 60,
        block_duration: int = 300
    ) -> Tuple[bool, str]:
        """
        Проверить rate limit для пользователя
        
        Args:
            user_id: ID пользователя
            max_requests: Максимальное количество запросов
            time_window: Временное окно в секундах
            block_duration: Длительность блокировки в секундах
        
        Returns:
            (is_allowed, message)
        """
        current_time = time.time()
        
        # Проверяем, не заблокирован ли пользователь
        if user_id in self._blocked:
            unblock_time = self._blocked[user_id]
            if current_time < unblock_time:
                remaining = int(unblock_time - current_time)
                return False, f"⏳ Вы временно заблокированы. Попробуйте через {remaining} секунд"
            else:
                # Разблокируем
                del self._blocked[user_id]
                self._violations[user_id] = 0
        
        # Очищаем старые запросы
        cutoff_time = current_time - time_window
        user_requests = self._requests[user_id]
        user_requests[:] = [req_time for req_time in user_requests if req_time > cutoff_time]
        
        # Проверяем лимит
        if len(user_requests) >= max_requests:
            # Блокируем пользователя
            self._blocked[user_id] = current_time + block_duration
            self._violations[user_id] += 1
            logger.warning(f"🚫 Пользователь {user_id} заблокирован за превышение лимита запросов")
            return False, f"⛔ Превышен лимит запросов. Блокировка на {block_duration} секунд"
        
        # Добавляем текущий запрос
        user_requests.append(current_time)
        return True, ""
    
    def check_action_rate_limit(
        self,
        user_id: int,
        action: str,
        max_requests: int = 5,
        time_window: int = 30
    ) -> Tuple[bool, str]:
        """
        Проверить rate limit для конкретного действия
        
        Args:
            user_id: ID пользователя
            action: Название действия
            max_requests: Максимальное количество запросов
            time_window: Временное окно в секундах
        
        Returns:
            (is_allowed, message)
        """
        current_time = time.time()
        key = f"{user_id}:{action}"
        
        # Очищаем старые запросы
        cutoff_time = current_time - time_window
        requests = self._requests.get(key, [])
        requests[:] = [req_time for req_time in requests if req_time > cutoff_time]
        
        # Проверяем лимит
        if len(requests) >= max_requests:
            logger.warning(f"🚫 Пользователь {user_id} превысил лимит для действия '{action}'")
            return False, f"⏳ Слишком много запросов. Подождите {time_window} секунд"
        
        # Добавляем текущий запрос
        if key not in self._requests:
            self._requests[key] = []
        self._requests[key].append(current_time)
        return True, ""
    
    def is_blocked(self, user_id: int) -> bool:
        """Проверить, заблокирован ли пользователь"""
        if user_id not in self._blocked:
            return False
        
        current_time = time.time()
        if current_time >= self._blocked[user_id]:
            del self._blocked[user_id]
            return False
        
        return True
    
    def get_violations_count(self, user_id: int) -> int:
        """Получить количество нарушений пользователя"""
        return self._violations.get(user_id, 0)
    
    def reset_user(self, user_id: int):
        """Сбросить статистику пользователя"""
        if user_id in self._requests:
            del self._requests[user_id]
        if user_id in self._blocked:
            del self._blocked[user_id]
        if user_id in self._violations:
            del self._violations[user_id]


# Глобальные экземпляры rate limiters для разных типов действий
message_rate_limiter = RateLimiter()  # Для текстовых сообщений
callback_rate_limiter = RateLimiter()  # Для callback queries
registration_rate_limiter = RateLimiter()  # Для регистрации
admin_rate_limiter = RateLimiter()  # Для админ-панели


def check_message_rate_limit(user_id: int) -> Tuple[bool, str]:
    """Проверить rate limit для сообщений"""
    return message_rate_limiter.check_rate_limit(
        user_id=user_id,
        max_requests=15,  # 15 сообщений
        time_window=60,   # в минуту
        block_duration=300  # блокировка на 5 минут
    )


def check_callback_rate_limit(user_id: int) -> Tuple[bool, str]:
    """Проверить rate limit для callback queries"""
    return callback_rate_limiter.check_rate_limit(
        user_id=user_id,
        max_requests=30,  # 30 callback'ов
        time_window=60,   # в минуту
        block_duration=180  # блокировка на 3 минуты
    )


def check_registration_rate_limit(user_id: int) -> Tuple[bool, str]:
    """Проверить rate limit для регистрации"""
    return registration_rate_limiter.check_action_rate_limit(
        user_id=user_id,
        action="registration",
        max_requests=3,  # 3 попытки
        time_window=300  # за 5 минут
    )


def check_admin_rate_limit(user_id: int) -> Tuple[bool, str]:
    """Проверить rate limit для админ-панели"""
    return admin_rate_limiter.check_rate_limit(
        user_id=user_id,
        max_requests=50,  # 50 запросов
        time_window=60,   # в минуту
        block_duration=600  # блокировка на 10 минут
    )


def check_content_keyword_rate_limit(user_id: int) -> Tuple[bool, str]:
    """Проверить rate limit для поиска по ключевым словам"""
    return message_rate_limiter.check_action_rate_limit(
        user_id=user_id,
        action="content_keyword",
        max_requests=10,  # 10 запросов
        time_window=60    # в минуту
    )


def check_broadcast_rate_limit(user_id: int) -> Tuple[bool, str]:
    """Проверить rate limit для рассылки"""
    return admin_rate_limiter.check_action_rate_limit(
        user_id=user_id,
        action="broadcast",
        max_requests=1,   # 1 рассылка
        time_window=300   # за 5 минут
    )

