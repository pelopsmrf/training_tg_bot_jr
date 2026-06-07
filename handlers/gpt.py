import logging
from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.chat_gpt import ChatGPTService
from utils.random_fox import fox
from handlers.common import start_keyboard


gpt_router = Router()

class GptCommands(StatesGroup):
    gpt_command = State()

@gpt_router.message(Command('gpt'))
async def command_gpt(message: types.Message, state: FSMContext):
    await state.clear()
    image_fox = await fox()
    if image_fox:
        await message.answer_photo(image_fox)
    await message.answer("🤖 Режим ChatGPT включён!\nЗадайте мне любой вопрос:")
    await state.set_state(GptCommands.gpt_command)

@gpt_router.message(StateFilter(GptCommands.gpt_command), F.text)
async def command_gpt(message: types.Message, chat_gpt_service: ChatGPTService, state: FSMContext):
    # Проверка длины сообщения
    if len(message.text) > 2000:
        await message.answer("⚠️ Слишком длинное сообщение. Пожалуйста, сократите до 2000 символов.")
        await state.set_state(GptCommands.gpt_command)
        return

    system = "Коротко отвечай на вопросы"
    try:
        response = await chat_gpt_service.ask_gpt(system=system, question=message.text)
        if response:
            await message.answer(response, reply_markup=start_keyboard)
        else:
            await message.answer("❌ Не удалось получить ответ от ChatGPT. Попробуйте позже.", reply_markup=start_keyboard)
    except Exception as e:
        logging.error(f"Ошибка в GPT хендлере: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.", reply_markup=start_keyboard)
    await state.set_state(GptCommands.gpt_command)

@gpt_router.message(Command('cancel'))
async def cancel_gpt(message: types.Message, state: FSMContext):
    """Отмена режима GPT"""
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("❌ Режим ChatGPT отменён", reply_markup=start_keyboard)
