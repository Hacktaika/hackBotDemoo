# Инструкция по установке

## Проблема с Python 3.13

`aiogram 3.4.1` требует `pydantic<2.6`, но для Python 3.13 нужна более новая версия pydantic. 

**Решение: используйте Python 3.12 или ниже**

## Установка Python 3.12

### macOS (через Homebrew):
```bash
brew install python@3.12
```

### Создание виртуального окружения с Python 3.12:
```bash
# Удалите старое окружение если есть
rm -rf .venv

# Создайте новое с Python 3.12
python3.12 -m venv .venv

# Активируйте
source .venv/bin/activate

# Установите зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

### Альтернатива: через pyenv
```bash
# Установите pyenv если нет
brew install pyenv

# Установите Python 3.12
pyenv install 3.12.7

# Установите как локальную версию
pyenv local 3.12.7

# Создайте окружение
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## После установки

1. Создайте `.env` файл из `.env.example`
2. Заполните все необходимые переменные
3. Запустите бота:
```bash
python bot.py
```

