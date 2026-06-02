from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply import get_keyboard
from keyboards.keyboards import keyboard_end
from services.chat_gpt import ChatGPTService
from utils.random_fox import fox


talk_router = Router()

talk_keyboard = get_keyboard(
    "Конфуций",
    "Иммануил Кант",
    "Аристотель",
    "Платон",
    placeholder="Выберите философа для разговора",
    sizes=(2, 2)
)

philosophers = {
    "Конфуций": "Ты - Конфуций, древнекитайский философ и мыслитель, основатель конфуцианства. Ты известен своими учениями о морали, этике, социальной гармонии и правильном поведении. Ты стремишься помочь людям жить в гармонии с собой и окружающим миром, следуя принципам добродетели, уважения и справедливости.",
    "Иммануил Кант": "Ты - Иммануил Кант, немецкий философ, основатель критической философии. Ты известен своими учениями о морали, этике и знании. Ты стремишься помочь людям понять природу морали и правильного поведения.",
    "Аристотель": "Ты - Аристотель, древнегреческий философ. Ты известен своими учениями о логике, этике, политики и природе вещей. Ты стремишься помочь людям понять мир вокруг них.",
    "Платон": "Ты - Платон, древнегреческий философ. Ты известен своими учениями о идеях, этике и политике. Ты стремишься помочь людям понять природу реальности."
}

class TalkStates(StatesGroup):
    waiting_for_philosopher = State()
    waiting_for_question = State()

@talk_router.message(Command('talk'))
async def command_random(message: types.Message, state: FSMContext):
    image_fox = fox()
    await message.answer("Выберите философа для разговора:", reply_markup=talk_keyboard)
    await state.set_state(TalkStates.waiting_for_philosopher)

@talk_router.message(TalkStates.waiting_for_philosopher, F.text.in_(philosophers.keys()))
async def command_random(message: types.Message, chat_gpt_service: ChatGPTService, state: FSMContext):
    system = philosophers.get(message.text)
    await state.update_data(system=system)
    response = await chat_gpt_service.ask_gpt(system=system, question=message.text)
    await message.answer(response, reply_markup=keyboard_end)
    await state.set_state(TalkStates.waiting_for_question)