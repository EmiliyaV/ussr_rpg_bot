Реализованные пункты MVP-архитектуры

1. Правила игры зафиксированы:
   - роли лежат в app/content/roles.py;
   - годы, вопросы, варианты и эффекты лежат в app/content/history.py;
   - скрытые статы и диапазон -10..10 лежат в app/game/rules.py;
   - условия проигрыша и финала лежат в app/game/engine.py.

2. История остаётся в коде:
   - app/content/history.py
   - JSON/MD не используются.

3. Скрытые статы:
   - GameState содержит user_id, role_id, turn, stats, memory, status, ending_type.
   - Игроку числа не показываются через /status.

4. Пересчёт статов:
   - GameEngine._apply_effects()
   - LLM не участвует в расчётах.

5. Интерпретатор эффектов:
   - app/game/consequence_interpreter.py

6. Интерпретатор состояния:
   - app/game/stat_interpreter.py

7. Prompt для Ollama:
   - app/llm/prompts.py
   - Ollama получает исторический контекст, роль, выбор, смысл изменений, состояние после выбора и память.

8. Fallback:
   - app/game/fallback_narrator.py
   - Не показывает числа и технические названия метрик.

9. /status и /debug_status:
   - /status показывает состояние без чисел.
   - /debug_status показывает скрытые числа для отладки.

10. Финал:
   - тип финала выбирает код;
   - Ollama только формулирует финальный текст;
   - fallback-финал тоже без чисел.

Проверка:
python scripts/check_project_steps.py

Запуск:
python -m app.main
