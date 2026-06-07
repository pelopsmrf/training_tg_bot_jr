import json
import logging
import re
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

Формат вывода (строго JSON, без дополнительного текста):
{
    "question": "Текст вопроса",
    "options": {
        "A": "Вариант A",
        "B": "Вариант B",
        "C": "Вариант C",
        "D": "Вариант D"
    },
    "correct": "A"
}
"""

class TalkStates(StatesGroup):
    waiting_for_quiz = State()
    waiting_for_answer = State()
    score = State()


@quiz_router.message(Command("quiz"))
async def command_quiz(message: types.Message, state: FSMContext):
    await state.clear()
    image_fox = await fox()
    if image_fox:
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
    
    try:
        response = await chat_gpt_service.ask_gpt(system=system_quiz, question=selected_topic)
        if not response:
            await message.answer("❌ Не удалось сгенерировать вопрос. Попробуйте другую тему.")
            return
        
        # Парсим JSON ответ
        question_data = parse_quiz_response(response)
        
        if question_data:
            await state.update_data(question_data=question_data)
            await state.update_data(correct_answer=question_data["correct"])
            
            # Форматируем вопрос для отображения
            formatted_question = (
                f"❓ {question_data['question']}\n\n"
                f"A) {question_data['options']['A']}\n"
                f"B) {question_data['options']['B']}\n"
                f"C) {question_data['options']['C']}\n"
                f"D) {question_data['options']['D']}"
            )
            
            await message.answer(formatted_question, reply_markup=types.ReplyKeyboardRemove())
            await message.answer("📝 Введите ваш ответ (A, B, C или D):")
            await state.set_state(TalkStates.waiting_for_answer)
        else:
            # Fallback: показываем сырой ответ
            await state.update_data(current_question=response)
            match = re.search(r'✅ Правильный ответ:\s*([A-D])', response)
            if match:
                await state.update_data(correct_answer=match.group(1))
            
            await message.answer(response, reply_markup=types.ReplyKeyboardRemove())
            await message.answer("📝 Введите ваш ответ (A, B, C или D):")
            await state.set_state(TalkStates.waiting_for_answer)
            
    except Exception as e:
        logging.error(f"Ошибка в quiz хендлере: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте ещё раз.")


def parse_quiz_response(response: str) -> dict | None:
    """Парсинг JSON ответа от ChatGPT для квиза"""
    # Пробуем найти JSON в ответе
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if all(k in data for k in ("question", "options", "correct")):
                return data
        except json.JSONDecodeError:
            pass
    return None


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
    
    try:
        response = await chat_gpt_service.ask_gpt(system=system_quiz, question=current_topic)
        
        # Удаляем сообщение о загрузке
        await loading_msg.delete()
        
        if not response:
            await message.answer("❌ Не удалось сгенерировать вопрос. Попробуйте ещё раз.")
            return
        
        # Парсим JSON ответ
        question_data = parse_quiz_response(response)
        
        if question_data:
            await state.update_data(question_data=question_data)
            await state.update_data(correct_answer=question_data["correct"])
            
            formatted_question = (
                f"❓ {question_data['question']}\n\n"
                f"A) {question_data['options']['A']}\n"
                f"B) {question_data['options']['B']}\n"
                f"C) {question_data['options']['C']}\n"
                f"D) {question_data['options']['D']}"
            )
            
            await message.answer(formatted_question)
            await message.answer("📝 Введите ваш ответ (A, B, C или D):")
            await state.set_state(TalkStates.waiting_for_answer)
        else:
            # Fallback: старый формат
            await state.update_data(current_question=response)
            match = re.search(r'✅ Правильный ответ:\s*([A-D])', response)
            if match:
                await state.update_data(correct_answer=match.group(1))
            
            await message.answer(response)
            await message.answer("📝 Введите ваш ответ (A, B, C или D):")
            await state.set_state(TalkStates.waiting_for_answer)
            
    except Exception as e:
        logging.error(f"Ошибка при генерации вопроса: {e}")
        await loading_msg.delete()
        await message.answer("❌ Произошла ошибка. Попробуйте ещё раз.")


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

@quiz_router.message(Command('cancel'))
async def cancel_quiz(message: types.Message, state: FSMContext):
    """Отмена квиза"""
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("❌ Квиз завершён досрочно", reply_markup=start_keyboard)
