USSR RPG Bot MVP

Что уже есть:
- Telegram-бот на aiogram 3.
- Выбор роли.
- 3 игровых года: 1920, 1921, 1922.
- Вопросы, варианты и эффекты зашиты в Python-код.
- Метрики считает код, не LLM.
- Ollama используется только для генерации итогов года и финала.
- Если Ollama недоступна, бот работает через fallback.
- Состояние игроков хранится в SQLite.

Как запустить:

1. Создать виртуальное окружение:
   python -m venv .venv

2. Активировать:
   Windows PowerShell:
   .\.venv\Scripts\Activate.ps1

   Linux/macOS:
   source .venv/bin/activate

3. Установить зависимости:
   pip install -r requirements.txt

4. Создать .env:
   cp .env.example .env

   На Windows можно:
   copy .env.example .env

5. Вписать TELEGRAM_BOT_TOKEN в .env.

6. Опционально запустить Ollama:
   ollama pull llama3.2:3b
   ollama serve

7. Запустить бота:
   python -m app.main

Команды бота:
/start  — начать игру
/status — текущие показатели
/help   — справка
