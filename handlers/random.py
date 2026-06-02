from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.chat_gpt import ChatGPTService
from keyboards.reply import get_keyboard
from utils.random_fox import fox


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
    image_fox = fox()
    await message.answer_photo(image_fox)
    system = "Это команда для получения случайного ответа от OpenAI API."
    response = await chat_gpt_service.ask_gpt(system=system, question="Расскажи мне что-нибудь интересное!")
    await message.answer(response, reply_markup=random_keyboard)
    await state.set_state(RandomCommands.random_command)

@random_router.message(F.text == "Хочу еще факт")
async def command_random(message: types.Message, chat_gpt_service: ChatGPTService, state: FSMContext):
    system = "Это команда для получения случайного ответа от OpenAI API."
    response = await chat_gpt_service.ask_gpt(system=system, question="Расскажи мне что-нибудь интересное!")
    await message.answer(response, reply_markup=random_keyboard)
    await state.set_state(RandomCommands.random_command)