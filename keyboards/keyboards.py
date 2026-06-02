from aiogram import types


button_random = types.KeyboardButton(text="/random")
button_gpt = types.KeyboardButton(text="/gpt")

keyboard = types.ReplyKeyboardMarkup(keyboard=[[button_random, button_gpt]],
                                    resize_keyboard=True,
                                    one_time_keyboard=True)

keyboard_end = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="Закончить")]],
                                    resize_keyboard=True,
                                    one_time_keyboard=True)

# button_random_end = types.KeyboardButton(text="Закончить")
# button_random_continue = types.KeyboardButton(text="Хочу еще факт")

# keyboard_random = types.ReplyKeyboardMarkup(keyboard=[[button_random_continue], [button_random_end]],
#                                             resize_keyboard=True,
#                                             one_time_keyboard=True)

def keyboard_random(bottons: list[str]) -> types.ReplyKeyboardMarkup:
    row = [types.KeyboardButton(text=button) for button in bottons]
    return types.ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True, one_time_keyboard=True)