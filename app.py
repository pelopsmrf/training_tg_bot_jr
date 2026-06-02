import asyncio
import logging
from aiogram import Bot, Dispatcher
from services.chat_gpt import ChatGPTService
from handlers import common, interpreter, random, gpt, talk, quiz, interpreter, voice
import config


async def main():
    TOKIN_TG = config.token_telegram
    TOKEN_OPENAI = config.token_openai

    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=TOKIN_TG)
    dp = Dispatcher()

    chat_gpt_service = ChatGPTService(api_key=TOKEN_OPENAI)
    dp['chat_gpt_service'] = chat_gpt_service

    dp.include_router(common.router)
    dp.include_router(random.random_router)
    dp.include_router(talk.talk_router)
    dp.include_router(quiz.quiz_router)
    dp.include_router(interpreter.interpreter_router)
    dp.include_router(voice.voice_router)
    dp.include_router(gpt.gpt_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("Бот включен")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен!!!")