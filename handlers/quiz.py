from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply import get_keyboard
from handlers.common import start_keyboard
from services.chat_gpt import ChatGPTService
from utils.random_fox import fox

quiz_router = Router()

quiz_keyboard_start = get_keyboard(
    "Необычные места",
    "IT и гаджеты",
    "Физика и математика",
    "Наука и изобретения",
    placeholder="Выберите тему для квиза",
    sizes=(2, 2)
)

quiz_keyboard_continue = get_keyboard(
    "Ещё вопрос",
    "Сменить тему",
    "Закончить квиз",
    placeholder="Что дальше",
    sizes=(2, 1)
)

quiz_topic = [
    "Необычные места",
    "IT и гаджеты",
    "Физика и математика",
    "Наука и изобретения",
]

system_quiz = """
            Ты - ведущий квиза. Создай один интересный вопрос на указанную тему.
            
            Правила:
            - Вопрос должен быть понятным и интересным
            - 4 варианта ответа (A, B, C, D)
            - Четко укажи правильный ответ
            
            Формат вывода:
            ❓ [Вопрос]
            
            A) [Вариант A]
            B) [Вариант B]
            C) [Вариант C]
            D) [Вариант D]
            
            ✅ Правильный ответ: [буква]
            """

class TalkStates(StatesGroup):
    waiting_for_quiz = State()
    waiting_for_answer = State()
    score = State()


@quiz_router.message(Command("quiz"))
async def command_quiz(message: types.Message, state: FSMContext):
    await state.clear()
    image_fox = fox()
    await message.answer_photo(photo=image_fox)
    await message.answer("🎯 Добро пожаловать в квиз!\nВыберите тему:", 
                         reply_markup=quiz_keyboard_start)
    await state.set_state(TalkStates.waiting_for_quiz)

@quiz_router.message(F.text == "Сменить тему")
async def change_topic(message: types.Message, state: FSMContext):
    """Смена темы - возврат к выбору"""
    await message.answer("🔄 Выберите новую тему для квиза:", 
                         reply_markup=quiz_keyboard_start)
    await state.set_state(TalkStates.waiting_for_quiz)    

@quiz_router.message(TalkStates.waiting_for_quiz, F.text.in_(quiz_topic))
async def generate_question(message: types.Message, chat_gpt_service: ChatGPTService, state: FSMContext):
    """Генерация вопроса по выбранной теме"""
    selected_topic = message.text
    
    # Сохраняем тему в контекст
    await state.update_data(current_topic=selected_topic)
    
    response = await chat_gpt_service.ask_gpt(system=system_quiz, question=selected_topic)
    
    # Сохраняем вопрос и правильный ответ
    await state.update_data(current_question=response)
    
    # Простой парсинг правильного ответа
    import re
    match = re.search(r'✅ Правильный ответ:\s*([A-D])', response)
    if match:
        await state.update_data(correct_answer=match.group(1))
    
    await message.answer(response, reply_markup=types.ReplyKeyboardRemove())
    await message.answer("📝 Введите ваш ответ (A, B, C или D):")
    await state.set_state(TalkStates.waiting_for_answer)


@quiz_router.message(F.text == "Ещё вопрос")
async def another_question(message: types.Message, chat_gpt_service: ChatGPTService, state: FSMContext):
    """Генерация нового вопроса по той же теме"""
    # Получаем сохраненную тему
    user_data = await state.get_data()
    current_topic = user_data.get("current_topic")
    
    if not current_topic:
        # Если тема не сохранена, просим выбрать заново
        await message.answer("⚠️ Пожалуйста, сначала выберите тему командой /quiz")
        return
    
    # Отправляем уведомление
    loading_msg = await message.answer("🔄 Генерирую новый вопрос...")
    
    response = await chat_gpt_service.ask_gpt(system=system_quiz, question=current_topic)
    
    # Удаляем сообщение о загрузке
    await loading_msg.delete()
    
    # Сохраняем новый вопрос и правильный ответ
    await state.update_data(current_question=response)
    
    import re
    match = re.search(r'✅ Правильный ответ:\s*([A-D])', response)
    if match:
        await state.update_data(correct_answer=match.group(1))
    
    await message.answer(response)
    await message.answer("📝 Введите ваш ответ (A, B, C или D):")
    await state.set_state(TalkStates.waiting_for_answer)


@quiz_router.message(TalkStates.waiting_for_answer, F.text.upper().in_(["A", "B", "C", "D"]))
async def check_answer(message: types.Message, chat_gpt_service: ChatGPTService, state: FSMContext):
    """Проверка ответа пользователя"""
    user_answer = message.text.upper()
    user_data = await state.get_data()
    correct_answer = user_data.get("correct_answer")
    current_question = user_data.get("current_question")
    
    if not correct_answer:
        await message.answer("❌ Ошибка! Пожалуйста, начните квиз заново командой /quiz")
        await state.clear()
        return
    
    if user_answer == correct_answer:
        score = user_data.get("score", 0) + 1
        await state.update_data(score=score)
        response = f"✅ Верно! Счёт: {score} 🎯"
    else:
        response = f"❌ **Неверно!** \n\nПравильный ответ: **{correct_answer}**\n\nПопробуйте следующий вопрос!"
    
    await message.answer(response, reply_markup=quiz_keyboard_continue)
    
    # Очищаем данные о предыдущем вопросе, но сохраняем тему
    await state.update_data(current_question=None, correct_answer=None)

@quiz_router.message(StateFilter("*"), F.text == "Закончить квиз")
async def end_quiz(message: types.Message, state: FSMContext):
    """Завершение квиза"""
    await message.answer(
        "🏆 **Спасибо за игру!** 🏆\n\n"
        "Возвращайтесь ещё, чтобы проверить свои знания!\n"
        "Команда /quiz - начать новый квиз",
        reply_markup=start_keyboard
    )
    await state.clear()

@quiz_router.message(StateFilter(TalkStates.waiting_for_answer))
async def invalid_answer_format(message: types.Message):
    """Некорректный формат ответа"""
    await message.answer("⚠️ Пожалуйста, введите ответ в формате: **A**, **B**, **C** или **D**")