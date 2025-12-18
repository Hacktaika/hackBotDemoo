FROM python:3.12-slim

# Установка рабочей директории
WORKDIR /app

# Установка системных зависимостей (если нужны)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Копирование файла зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование всего кода проекта
COPY . .

# Создание директории для данных БД (если её нет)
RUN mkdir -p /app/data

# Установка переменных окружения по умолчанию (можно переопределить через docker-compose)
ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/app/data/bot.db

# Запуск бота
CMD ["python", "bot.py"]

