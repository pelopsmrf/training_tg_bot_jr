# Telegram ChatGPT Bot

Telegram-бот с интеграцией OpenAI API (ChatGPT). Учебный проект.

## Возможности

- **/start** — Главное меню с кнопками всех команд (сбрасывает активные состояния)
- **/random** — Случайный интересный факт от ChatGPT
- **/gpt** — Диалог с ChatGPT (задавайте любые вопросы)
- **/talk** — Диалог с известными философами (Конфуций, Кант, Аристотель, Платон)
- **/quiz** — Квиз на разные темы с подсчётом очков
- **/interpreter** — Переводчик текста на 6 языков
- **/voice** — Голосовой режим (отправьте голосовое — получите голосовой ответ)
- **/clear** — Очистить историю диалога в голосовом режиме
- **/cancel** — Отмена текущего режима (работает во всех режимах)

## Архитектура проекта

```
training_tg_bot_jr/
├── app.py                  # Точка входа, инициализация бота и роутеров
├── config.py               # Загрузка переменных окружения из .env
├── requirements.txt        # Зависимости проекта
├── .env.example            # Пример файла с токенами
├── handlers/               # Обработчики команд (роутеры aiogram)
│   ├── common.py           # /start, главное меню
│   ├── gpt.py              # /gpt — диалог с ChatGPT
│   ├── random.py           # /random — случайные факты
│   ├── talk.py             # /talk — разговор с философами
│   ├── quiz.py             # /quiz — викторина
│   ├── interpreter.py      # /interpreter — переводчик
│   └── voice.py            # /voice — голосовой режим (Whisper + TTS)
├── keyboards/              # Клавиатуры для бота
│   ├── keyboards.py        # Готовые клавиатуры (keyboard_end)
│   └── reply.py            # Утилита для создания Reply-клавиатур
├── services/               # Бизнес-логика
│   └── chat_gpt.py         # ChatGPTService — обёртка над OpenAI API
└── utils/                  # Вспомогательные утилиты
    └── random_fox.py       # Случайное изображение лисы (с fallback)
```

### Ключевые решения

- **FSM (Finite State Machine)** — многошаговые сценарии (перевод, квиз, диалог) реализованы через состояния aiogram
- **Единый сервис ChatGPT** — `ChatGPTService` используется во всех текстовых хендлерах (кроме voice, где нужен прямой доступ к Whisper/TTS)
- **Обработка ошибок** — все запросы к API обёрнуты в try/except с логированием
- **Безопасность** — токены хранятся в `.env`, файл добавлен в `.gitignore`

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/pelopsmrf/training_tg_bot_jr.git
cd training_tg_bot_jr
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```
TOKEN_TG=your_telegram_bot_token
TOKEN_OPENAI=your_openai_api_key
```

4. Запустите бота:
```bash
python app.py
```

## Требования

- Python 3.10+
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- OpenAI API Key

## Используемые технологии

- [aiogram](https://docs.aiogram.dev/) 3.x — асинхронная библиотека для Telegram Bot API
- [OpenAI Python SDK](https://github.com/openai/openai-python) — работа с ChatGPT, Whisper, TTS
- [aiohttp](https://docs.aiohttp.org/) — асинхронные HTTP-запросы
- [python-dotenv](https://github.com/theskumar/python-dotenv) — управление переменными окружения
- [pydub](https://github.com/jiaaro/pydub) — обработка аудио (для голосового режима)
