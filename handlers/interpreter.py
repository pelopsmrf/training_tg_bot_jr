from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.chat_gpt import ChatGPTService
from keyboards.reply import get_keyboard
from utils.random_fox import fox


interpreter_router = Router()

interpreter_keyboard = get_keyboard(
    "Английский",
    "Испанский",
    "Турецкий",
    "Греческий",
    "Арабский",
    "Китайский",
    placeholder="Выбери язык для перевода",
    sizes=(2, 2, 2)
)

# Клавиатура с действиями после перевода
action_keyboard = get_keyboard(
    "🔄 Новый перевод",
    "🌍 Сменить язык",
    "❌ Завершить",
    placeholder="Выберите действие:",
    sizes=(2, 1)
)

languages = {
    "Английский": "English",
    "Испанский": "Spanish",
    "Турецкий": "Turkish",
    "Греческий": "Greek",
    "Арабский": "Arabic",
    "Китайский": "Chinese"
}

class InterpreterCommands(StatesGroup):
    translation_language = State()
    waiting_for_text = State()
    translator_mode = State()

@interpreter_router.message(Command('interpreter'))
async def start_interpreter(message: types.Message, state: FSMContext):
    image_fox = fox()
    await message.answer_photo(image_fox)
    await message.answer("Добро пожаловать в переводчик!\nВыберите язык пеервода:", 
                         reply_markup=interpreter_keyboard)
    await state.set_state(InterpreterCommands.translation_language)

@interpreter_router.message(InterpreterCommands.translation_language, F.text.in_(languages.keys()))
async def language_selected(message: types.Message, state: FSMContext):
    selected_language_ru = message.text
    selected_language_en = languages[selected_language_ru]
    
    await state.update_data(
        target_language_ru=selected_language_ru,
        target_language_en=selected_language_en
    )
    
    await message.answer(
        f"✅ Выбран язык: {selected_language_ru}\n"
        f"📝 Теперь отправьте текст для перевода с русского на {selected_language_ru}:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(InterpreterCommands.waiting_for_text)

@interpreter_router.message(InterpreterCommands.waiting_for_text, F.text)
async def translate_text(
    message: types.Message, 
    chat_gpt_service: ChatGPTService, 
    state: FSMContext
):
    """Выполнение перевода"""
    user_data = await state.get_data()
    target_language_ru = user_data.get('target_language_ru')
    target_language_en = user_data.get('target_language_en')
    
    # Отправляем статус "печатает"
    await message.bot.send_chat_action(message.chat.id, action="typing")
    
    # Формируем запрос для GPT
    system_prompt = (
        f"Ты профессиональный переводчик. Переводи текст с русского языка "
        f"на {target_language_en} ({target_language_ru}). "
        f"Переводи точно, сохраняя смысл и стиль оригинала. "
        f"Возвращай только перевод без дополнительных комментариев."
    )
    
    try:
        response = await chat_gpt_service.ask_gpt(
            system=system_prompt, 
            question=message.text
        )
        
        # Форматируем ответ
        result = (
            f"🔍 **Перевод с русского на {target_language_ru}**\n\n"
            f"📝 **Оригинал:**\n{message.text}\n\n"
            f"✅ **Перевод:**\n{response}"
        )
        
        await message.answer(result, reply_markup=action_keyboard)
        await state.set_state(InterpreterCommands.translator_mode)
        
    except Exception as e:
        await message.answer(
            "❌ Ошибка при переводе. Попробуйте еще раз.",
            reply_markup=action_keyboard
        )

@interpreter_router.message(InterpreterCommands.translator_mode, F.text == "🔄 Новый перевод")
async def new_translation(message: types.Message, state: FSMContext):
    """Новый перевод на текущий язык"""
    await message.answer(
        "📝 Отправьте новый текст для перевода:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(InterpreterCommands.waiting_for_text)

@interpreter_router.message(InterpreterCommands.translator_mode, F.text == "🌍 Сменить язык")
async def change_language(message: types.Message, state: FSMContext):
    """Сменить язык перевода"""
    await message.answer(
        "🌍 Выберите новый язык для перевода:",
        reply_markup=interpreter_keyboard
    )
    await state.set_state(InterpreterCommands.translation_language)

@interpreter_router.message(InterpreterCommands.translator_mode, F.text == "❌ Завершить")
async def finish_translator(message: types.Message, state: FSMContext):
    """Завершить работу переводчика"""
    await state.clear()
    await message.answer(
        "👋 Работа переводчика завершена.\n"
        "Для нового запуска используйте /interpreter",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Обработчик для отмены и других команд
@interpreter_router.message(Command('cancel'))
async def cancel_command(message: types.Message, state: FSMContext):
    """Отмена текущей операции"""
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await message.answer(
        "❌ Операция отменена",
        reply_markup=types.ReplyKeyboardRemove()
    )