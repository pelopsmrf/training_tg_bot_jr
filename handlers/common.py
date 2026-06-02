from aiogram import Router, types, F
from aiogram.filters import Command

from keyboards.keyboards import keyboard
from keyboards.reply import get_keyboard

router = Router()

start_keyboard = get_keyboard(
    "/random",
    "/gpt",
    "/talk",
    "/quiz",
    "/interpreter",
    "/voice",
    placeholder="Что хотите сделать?",
    sizes=(2, 2, 1)
)

@router.message(Command('start'))
@router.message(F.text.in_("Закончить"))
async def command_start(message: types.Message):
    await message.answer(f"Привет, {message.chat.first_name}!\
                         \nЯ бот, который использует OpenAI API. Чем я могу помочь?",
                         reply_markup=start_keyboard)
