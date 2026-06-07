import os
import tempfile
import logging
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from openai import AsyncOpenAI
from services.chat_gpt import ChatGPTService

import config

TOKEN_OPENAI = config.token_openai

voice_router = Router()
open_client = AsyncOpenAI(api_key=TOKEN_OPENAI)

# Храним историю диалогов (в памяти, для простоты)
# Ключ: user_id, Значение: список сообщений
chat_histories: dict[int, list[dict]] = {}
MAX_HISTORY = 10  # Сколько пар вопрос-ответ хранить

# Системный промпт для голосового ассистента
VOICE_SYSTEM_PROMPT = (
    "Ты дружелюбный голосовой ассистент. "
    "Отвечай кратко и по делу, как если бы ты говорил голосом. "
    "Избегай длинных абзацев, списков и markdown-форматирования — "
    "твой ответ будет озвучен."
)


def _init_history(user_id: int) -> None:
    """Инициализировать историю диалога для пользователя"""
    if user_id not in chat_histories:
        chat_histories[user_id] = [
            {"role": "system", "content": VOICE_SYSTEM_PROMPT}
        ]


def _trim_history(user_id: int) -> None:
    """Обрезать историю, если слишком длинная"""
    if len(chat_histories[user_id]) > MAX_HISTORY * 2 + 1:
        # Оставляем system-сообщение + последние N пар
        chat_histories[user_id] = (
            [chat_histories[user_id][0]]
            + chat_histories[user_id][-(MAX_HISTORY * 2):]
        )


@voice_router.message(Command("voice"))
async def command_voice(message: types.Message):
    """Запуск голосового режима"""
    user_id = message.from_user.id
    _init_history(user_id)
    await message.answer(
        "🎤 Голосовой режим включён!\n"
        "Отправьте голосовое сообщение, и я отвечу вам голосом.\n"
        "Команда /clear — очистить историю диалога."
    )


@voice_router.message(F.voice)
async def handle_voice(message: types.Message):
    """Голосовое → текст → ChatGPT → голосовое"""
    processing_msg = await message.reply("🎙 Распознаю голосовое...")

    ogg_path = None
    tts_path = None

    try:
        # ─── ШАГ 1: Скачиваем голосовое от Telegram ───────────────────
        file = await message.bot.get_file(message.voice.file_id)
        ogg_data = await message.bot.download_file(file.file_path)

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f_ogg:
            f_ogg.write(ogg_data.read())
            ogg_path = f_ogg.name

        # ─── ШАГ 2: Whisper — речь → текст ────────────────────────────
        await processing_msg.edit_text("🎙 Распознаю речь...")

        with open(ogg_path, "rb") as audio_file:
            transcript = await open_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"
            )

        user_text = transcript.text

        if not user_text.strip():
            await processing_msg.edit_text("❌ Не удалось распознать речь. Попробуйте ещё.")
            return

        # Показываем распознанный текст
        await processing_msg.edit_text(
            f"📝 <b>Вы сказали:</b>\n{user_text}\n\n🤖 Думаю над ответом..."
        )

        # ─── ШАГ 3: ChatGPT — текст → ответ ───────────────────────────
        user_id = message.from_user.id
        _init_history(user_id)

        # Добавляем сообщение пользователя в историю
        chat_histories[user_id].append({"role": "user", "content": user_text})
        _trim_history(user_id)

        gpt_response = await open_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_histories[user_id],
            max_tokens=1000,
        )

        assistant_text = gpt_response.choices[0].message.content

        # Сохраняем ответ в историю
        chat_histories[user_id].append({"role": "assistant", "content": assistant_text})

        # ─── ШАГ 4: TTS — текст → речь ────────────────────────────────
        await processing_msg.edit_text("🔊 Озвучиваю ответ...")

        tts_response = await open_client.audio.speech.create(
            model="tts-1",
            voice="alloy",       # alloy / echo / fable / onyx / nova / shimmer
            input=assistant_text,
            response_format="ogg",  # Telegram голосовые = OGG Opus
        )

        # Сохраняем аудио во временный файл
        tts_path = ogg_path.replace(".ogg", "_tts.ogg")
        with open(tts_path, "wb") as f_tts:
            f_tts.write(tts_response.content)

        # ─── ШАГ 5: Отправляем голосовое + текст пользователю ─────────
        voice_file = FSInputFile(tts_path, filename="response.ogg")
        await message.answer_voice(voice_file)

        # Затем текст (для наглядности)
        await processing_msg.edit_text(
            f"📝 <b>Вы:</b> {user_text}\n\n"
            f"🤖 <b>ChatGPT:</b> {assistant_text}"
        )

    except Exception as e:
        logging.error(f"Ошибка в voice хендлере: {e}")
        await processing_msg.edit_text(f"❌ Ошибка: {str(e)}")

    finally:
        # Удаляем временные файлы
        if ogg_path and os.path.exists(ogg_path):
            os.unlink(ogg_path)
        if tts_path and os.path.exists(tts_path):
            os.unlink(tts_path)


@voice_router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    """Очистить историю диалога"""
    user_id = message.from_user.id
    chat_histories.pop(user_id, None)
    await message.answer("🗑 История диалога очищена.")
