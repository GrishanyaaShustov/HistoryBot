import asyncio
import random

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery, Message
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from quesions import *

# --- Константы ---
API_TOKEN = '7984578993:AAHMYjG-H2F5cTPB5UMoN4c6ZzAof0PTCOc'

# --- Инициализация бота и диспетчера ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Темы (связываем ключи с вопросами) ---
THEMES = {
    "medieval": QUESTIONS["medieval"],
    "ussr": QUESTIONS["ussr"],
    "rf": QUESTIONS["rf"]
}

# --- Хранилище данных пользователя ---
user_data = {}

@dp.message(Command("start"))
async def start_quiz(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🏰 Средневековье", callback_data="theme:medieval")
    builder.button(text="🟥 СССР", callback_data="theme:ussr")
    builder.button(text="🟦 РФ", callback_data="theme:rf")
    builder.adjust(1)

    await message.answer(
        "👋 Привет! Выбери тему викторины:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("theme:"))
async def choose_theme(callback: CallbackQuery):
    user_id = callback.from_user.id
    theme_key = callback.data.split(":")[1]

    user_data[user_id] = {
        "theme": theme_key,
        "score": 0,
        "question": None,
        "remaining": THEMES[theme_key].copy()
    }

    await callback.message.edit_text(f"📚 Тема выбрана: {theme_key.upper()}")
    await send_question(user_id)

async def send_question(user_id: int):
    data = user_data.get(user_id)
    if not data:
        return

    if not data["remaining"]:
        score = data["score"]
        await bot.send_message(
            user_id,
            f"🏁 Викторина завершена. Вы набрали <b>{score}</b> баллов.",
            parse_mode=ParseMode.HTML
        )
        await offer_restart(user_id)
        user_data.pop(user_id, None)
        return

    question = random.choice(data["remaining"])
    data["remaining"].remove(question)
    data["question"] = question

    kb = InlineKeyboardBuilder()
    for opt in question["options"]:
        kb.button(text=opt, callback_data=f"answer:{opt}")
    kb.button(text="⏭ Пропустить", callback_data="skip")
    kb.button(text="🛑 Завершить", callback_data="stop")
    kb.adjust(2)

    await bot.send_message(
        user_id,
        f"🧠 <b>Вопрос:</b> {question['question']}",
        reply_markup=kb.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data.startswith("answer:") | F.data.in_(["skip", "stop"]))
async def handle_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = user_data.get(user_id)

    if not user:
        await callback.message.answer("⚠️ Вы ещё не начали викторину. Напишите /start")
        return

    data = callback.data

    if data == "stop":
        score = user["score"]
        await callback.message.edit_reply_markup()
        await callback.message.answer(
            f"🏁 Викторина завершена. Баллов: <b>{score}</b>",
            parse_mode=ParseMode.HTML
        )
        await offer_restart(user_id)
        user_data.pop(user_id, None)
        return

    if data == "skip":
        await callback.message.edit_reply_markup()
        await send_question(user_id)
        return

    selected_answer = data.split(":")[1]
    correct_answer = user["question"]["correct"]

    if selected_answer == correct_answer:
        user["score"] += 1
        text = "✅ Правильно!"
    else:
        text = f"❌ Неправильно. Правильный ответ: <b>{correct_answer}</b>"

    await callback.message.edit_reply_markup()
    await callback.message.answer(text, parse_mode=ParseMode.HTML)
    await send_question(user_id)

async def offer_restart(user_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🏰 Средневековье", callback_data="theme:medieval")
    kb.button(text="🟥 СССР", callback_data="theme:ussr")
    kb.button(text="🟦 РФ", callback_data="theme:rf")
    kb.adjust(1)

    await bot.send_message(
        user_id,
        "❓ Хотите начать новую викторину? Выберите тему:",
        reply_markup=kb.as_markup()
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
