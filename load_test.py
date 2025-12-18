"""
Простой скрипт нагрузочного тестирования для Hacktaika Bot.

Идея:
- Используем пользовательский Telegram-аккаунт через Telethon
- Эмулируем "много сообщений" к боту за короткое время
- Измеряем время ответа и проверяем, не валится ли бот

ВНИМАНИЕ:
- Нельзя "создать тысячи пользователей" из воздуха — Telegram этого не даёт.
- Поэтому мы эмулируем нагрузку количеством сообщений и действий от 1–нескольких аккаунтов.

Как использовать:
1. Установи дополнительные зависимости:
   pip install telethon

2. Получи api_id и api_hash:
   - Зайди на https://my.telegram.org
   - "API development tools" → создай приложение
   - Скопируй api_id и api_hash

3. Первый запуск:
   python load_test.py
   - Скрипт попросит ввести номер телефона
   - Telegram пришлёт код → введи его в консоль
   - После этого сессия сохранится в файле session.session

4. Запуск нагрузки:
   - Внизу файла настрой:
       BOT_USERNAME = "@your_bot_username"
       TOTAL_MESSAGES = 500       # общее количество сообщений
       CONCURRENCY = 10           # сколько "параллельных потоков"
       DELAY_BETWEEN_BATCHES = 0  # пауза между батчами, секунд

   - Запусти:
       python load_test.py

5. Смотри в консоль:
   - Среднее время ответа
   - Сколько запросов удалось отправить
   - Есть ли таймауты/ошибки (если много — бот/сервер не справляется)
"""

import asyncio
import time
from dataclasses import dataclass
from typing import List

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError


# Настройки клиента (заполни свои значения!)
API_ID = 123456          # <= сюда твой api_id (int)
API_HASH = "YOUR_API_HASH_HERE"  # <= сюда твой api_hash (str)
SESSION_NAME = "session"  # файл сессии (создастся автоматически)

# Настройки нагрузки
BOT_USERNAME = "@your_bot_username_here"  # <- сюда username твоего бота
TOTAL_MESSAGES = 300        # сколько всего сообщений отправить
CONCURRENCY = 10            # сколько одновременных "потоков" (корутин)
DELAY_BETWEEN_BATCHES = 0.0  # пауза между батчами (сек), можно увеличить
MESSAGE_TEXT = "test load message"  # текст сообщения
TIMEOUT_FOR_REPLY = 10.0    # сколько секунд ждать ответа бота


@dataclass
class Result:
    sent: int = 0
    errors: int = 0
    timeouts: int = 0
    latencies: List[float] = None

    def __post_init__(self):
        if self.latencies is None:
            self.latencies = []


async def send_and_wait_reply(client: TelegramClient, bot_username: str, text: str, timeout: float, result: Result):
    """
    Отправляем сообщение боту и ждём первый ответ в ответ на это сообщение.
    """
    try:
        # Отправляем сообщение и запоминаем время
        start = time.perf_counter()
        msg = await client.send_message(bot_username, text)

        # Ждём ответ, который является reply на наше сообщение
        @client.on(events.NewMessage(from_users=bot_username))
        async def handler(event):
            # оставляем хэндлер пустым: он нужен только чтобы Telethon "подписался" на новые сообщения
            ...

        try:
            response = await client.wait_for(
                events.NewMessage(from_users=bot_username),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            result.timeouts += 1
            return

        # Дополнительно можно проверить, что бот ответил именно на наше сообщение
        # if response.reply_to_msg_id != msg.id:
        #     return

        latency = time.perf_counter() - start
        result.latencies.append(latency)
        result.sent += 1

    except FloodWaitError as e:
        # Telegram просит подождать, когда мы слишком активно шлём
        print(f"[WARN] FloodWaitError: нужно подождать {e.seconds} секунд")
        result.errors += 1
        await asyncio.sleep(e.seconds + 1)
    except RPCError as e:
        print(f"[ERROR] RPCError: {e}")
        result.errors += 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        result.errors += 1


async def worker(client: TelegramClient, bot_username: str, messages_per_worker: int, result: Result):
    """
    Один "поток" нагрузки. Отправляет N сообщений подряд.
    """
    for i in range(messages_per_worker):
        await send_and_wait_reply(client, bot_username, f"{MESSAGE_TEXT} #{i}", TIMEOUT_FOR_REPLY, result)
        # небольшая микропаузa, чтобы не зафлудить сам Telegram-клиент
        await asyncio.sleep(0.05)


async def main():
    # Простые проверки, чтобы случайно не запустить с дефолтами
    if API_ID == 123456 or API_HASH == "YOUR_API_HASH_HERE":
        print("⚠️  Сначала заполни API_ID и API_HASH в load_test.py!")
        return
    if BOT_USERNAME == "@your_bot_username_here":
        print("⚠️  Сначала задай BOT_USERNAME (username твоего бота) в load_test.py!")
        return

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    print("🔌 Подключаемся к Telegram...")
    await client.start()  # при первом запуске попросит номер телефона и код
    me = await client.get_me()
    print(f"✅ Авторизован как: {me.first_name} (id={me.id})")

    # Распределяем общее количество сообщений на воркеры
    messages_per_worker = TOTAL_MESSAGES // CONCURRENCY
    remainder = TOTAL_MESSAGES % CONCURRENCY

    # Чтобы суммарно получилось TOTAL_MESSAGES, первым воркерам добавим по 1 сообщению
    messages_per_workers = [
        messages_per_worker + (1 if i < remainder else 0) for i in range(CONCURRENCY)
    ]

    print(
        f"🚀 Старт нагрузочного теста:\n"
        f"- Бот: {BOT_USERNAME}\n"
        f"- Всего сообщений: {TOTAL_MESSAGES}\n"
        f"- Воркеров: {CONCURRENCY}\n"
        f"- Сообщений на воркер: {messages_per_workers}\n"
    )

    result = Result()

    start_total = time.perf_counter()

    tasks = []
    for idx, cnt in enumerate(messages_per_workers):
        if cnt == 0:
            continue
        tasks.append(asyncio.create_task(worker(client, BOT_USERNAME, cnt, result)))

    # Можно запускать батчами, если хочешь паузы между "волнами"
    await asyncio.gather(*tasks)

    total_time = time.perf_counter() - start_total

    # Выводим статистику
    print("\n📊 Результаты нагрузочного теста:")
    print(f"- Всего попыток отправки: {TOTAL_MESSAGES}")
    print(f"- Успешно с ответом:      {result.sent}")
    print(f"- Ошибок:                 {result.errors}")
    print(f"- Таймаутов (нет ответа): {result.timeouts}")
    print(f"- Общее время теста:      {total_time:.2f} с")

    if result.latencies:
        avg_latency = sum(result.latencies) / len(result.latencies)
        max_latency = max(result.latencies)
        print(f"- Среднее время ответа:   {avg_latency:.2f} с")
        print(f"- Макс. время ответа:     {max_latency:.2f} с")
        rps = result.sent / total_time if total_time > 0 else 0
        print(f"- Пропускная способность: ~{rps:.2f} сообщений/сек")
    else:
        print("- Нет успешных ответов, проверь, работает ли бот и правильный ли BOT_USERNAME.")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())


