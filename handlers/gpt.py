from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.chat_gpt import ChatGPTService
from utils.random_fox import fox
from handlers.common import start_keyboard


gpt_router = Router()

class GptCommands(StatesGroup):
    gpt_command = State()

@gpt_router.message(Command('gpt'))
async def command_gpt(message: types.Message, chat_gpt_service: ChatGPTService, state: FSMContext):
    image_fox = fox()
    await message.answer_photo(image_fox)
    system = "Коротко отвечай на вопросы"
    response = await chat_gpt_service.ask_gpt(system=system, question=message.text)
    await message.answer(response, reply_markup=start_keyboard)
    await state.set_state(GptCommands.gpt_command)

@gpt_router.message(F.text)
async def command_gpt(message: types.Message, chat_gpt_service: ChatGPTService, state: FSMContext):
    system = "Коротко отвечай на вопросы"
    response = await chat_gpt_service.ask_gpt(system=system, question=message.text)
    await message.answer(response, reply_markup=start_keyboard)
    await state.set_state(GptCommands.gpt_command)