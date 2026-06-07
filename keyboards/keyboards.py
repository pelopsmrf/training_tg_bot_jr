from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


keyboard_end = (
    ReplyKeyboardBuilder()
    .add(KeyboardButton(text="Закончить"))
    .adjust(1)
    .as_markup(resize_keyboard=True, one_time_keyboard=True)
)
