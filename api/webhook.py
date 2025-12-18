"""
Serverless-эндпоинт для Vercel.

Идея:
- Vercel вызывает функцию `handler(request)` при каждом HTTP-запросе.
- Мы читаем JSON из тела запроса и передаём его в `webhook_app.process_update_sync`.

⚠️ Важно:
- Конкретный интерфейс `request` может отличаться в зависимости от версии Python-рантайма Vercel.
- Если Vercel ожидает другой формат, адаптируй чтение тела (см. документацию Vercel).
"""

import json
from typing import Any, Dict

from webhook_app import process_update_sync


def handler(request: Any) -> Dict[str, Any]:
    """
    Базовый пример обработчика для Vercel Python Function.

    Ожидается, что:
    - `request.body` содержит JSON от Telegram (bytes или str),
    - на выходе нужно вернуть dict с полями `statusCode`, `headers`, `body`.
    """
    raw_body = getattr(request, "body", b"")

    if isinstance(raw_body, bytes):
        raw_body = raw_body.decode("utf-8")

    if not raw_body:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "text/plain"},
            "body": "empty body",
        }

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "text/plain"},
            "body": "invalid json",
        }

    # Обработка апдейта бота (синхронная обёртка)
    process_update_sync(data)

    # Telegram ожидает быстрый 200 OK
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/plain"},
        "body": "ok",
    }


