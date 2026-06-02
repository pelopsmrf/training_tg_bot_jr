import os
from aiogram import F, Router, types
from aiogram.filters import Command
from openai import AsyncOpenAI
import tempfile

import config

TOKEN_OPENAI = config.token_openai

voice_router = Router()
open_client = AsyncOpenAI(api_key=TOKEN_OPENAI)  # Инициализируем OpenAI клиент для доступа к Whisper API

@voice_router.message(F.voice)
async def command_voice(message: types.Message):
    processing_msg = await message.reply("🎙 Распознаю голосовое...")

    ogg_path = None  # чтобы finally не падал, если файл не создался

    try:
        # 1. Скачиваем .ogg от Telegram
        file = await message.bot.get_file(message.voice.file_id)
        ogg_data = await message.bot.download_file(file.file_path)

        # 2. Сохраняем во временный файл (Whisper принимает .ogg!)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f_ogg:
            f_ogg.write(ogg_data.read())
            ogg_path = f_ogg.name

        # 3. Отправляем .ogg напрямую в Whisper (конвертация НЕ нужна)
        with open(ogg_path, "rb") as audio_file:
            transcript = await open_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"
            )

        text = transcript.text

        # 4. Ответ пользователю
        await processing_msg.edit_text(
            f"📝 <b>Текст сообщения:</b>\n{text}",
            parse_mode="HTML"
        )

    except Exception as e:
        await processing_msg.edit_text(f"❌ Ошибка: {str(e)}")

    finally:
        # 5. Гарантированно удаляем временный файл
        if ogg_path and os.path.exists(ogg_path):
            os.unlink(ogg_path)