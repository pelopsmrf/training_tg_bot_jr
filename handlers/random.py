import logging
from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.chat_gpt import ChatGPTService
from keyboards.reply import get_keyboard
from utils.random_fox import fox
from handlers.common import start_keyboard


random_router = Router()

random_keyboard = get_keyboard(
    "Хочу еще факт",
    "Закончить",
    placeholder="Что сделать",
    sizes=(2, )
)

class RandomCommands(StatesGroup):
    random_command = State()

@random_router.message(Command('random'))
async def command_random(message: types.Message, chat_gpt_service: ChatGPTService, state: FSMContext):
    await state.clear()
    image_fox = await fox()
    if image_fox:
        await message.answer_photo(image_fox)
    system = "Это команда для получения случайного ответа от OpenAI API."
    try:
        response = await chat_gpt_service.ask_gpt(system=system, question="Расскажи мне что-нибудь интересное!")
        if response:
            await message.answer(response, reply_markup=random_keyboard)
        else:
            await message.answer("❌ Не удалось получить ответ. Попробуйте позже.", reply_markup=random_keyboard)
    except Exception as e:
        logging.error(f"Ошибка в random хендлере: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.", reply_markup=random_keyboard)
    await state.set_state(RandomCommands.random_command)

@random_router.message(StateFilter(RandomCommands.random_command), F.text == "Хочу еще факт")
async def another_fact(message: types.Message, chat_gpt_service: ChatGPTService, state: FSMContext):
    system = "Это команда для получения случайного ответа от OpenAI API."
    try:
        response = await chat_gpt_service.ask_gpt(system=system, question="Расскажи мне что-нибудь интересное!")
        if response:
            await message.answer(response, reply_markup=random_keyboard)
        else:
            await message.answer("❌ Не удалось получить ответ. Попробуйте позже.", reply_markup=random_keyboard)
    except Exception as e:
        logging.error(f"Ошибка в random хендлере: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.", reply_markup=random_keyboard)
    await state.set_state(RandomCommands.random_command)

@random_router.message(Command('cancel'))
async def cancel_random(message: types.Message, state: FSMContext):
    """Отмена режима random"""
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("❌ Режим случайных фактов отменён", reply_markup=start_keyboard)
