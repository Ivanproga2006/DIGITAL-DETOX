from aiogram import Router
import sqlite3
from datetime import datetime
from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from program_days import program
from app import keyboards as kb
from config import bot

router = Router()

# Подключение к базе данных
conn = sqlite3.connect('social_detox.db')
cursor = conn.cursor()

# Создание таблиц (исправленные запросы)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    start_date TEXT,
    current_day INTEGER DEFAULT 1,
    total_saved_time INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    day INTEGER,
    completed BOOLEAN,
    timestamp TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
""")

conn.commit()


def get_day_confirmation_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✅ Задание выполнено",
        callback_data="day_completed"
    ))
    return builder.as_markup()


# Команда /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    # Проверяем, есть ли пользователь в базе
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        # Добавляем нового пользователя
        start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO users (user_id, username, full_name, start_date) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, start_date)
        )
        conn.commit()
        await message.answer(
            f"Привет, {full_name}! 👋\n"
            "Я буду твоим помощником в 30-дневном марафоне по снижению зависимости от соцсетей.\n\n"
            "Каждый день я буду давать тебе небольшое задание и поддерживать на этом пути.\n\n"
            "Готов начать? Нажми кнопку 'Сегодняшнее задание'!",
            reply_markup=kb.buttons
        )
    else:
        await message.answer(
            f"С возвращением, {full_name}! Рад снова тебя видеть. 😊\n"
            "Продолжаем наш марафон!",
            reply_markup=kb.buttons
        )

        # Отправляем задание текущего дня
        current_day = user[4]
        await send_day_task(user_id, current_day)


# Отправка задания дня
async def send_day_task(user_id, day):
    day_data = program.get(day)
    if not day_data:
        await bot.send_message(user_id, "Поздравляю! Вы завершили 30-дневный марафон! 🎉")
        return

    # Получаем информацию о пользователе
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        return

    # Отправляем сообщение с заданием
    await bot.send_message(
        user_id,
        f"🌟 {day_data['title']} 🌟\n\n"
        f"📌 Задание: {day_data['task']}\n\n"
        f"💪 Мотивация: {day_data['motivation']}\n\n"
        "Выполни задание и нажми кнопку ниже:",
        reply_markup=get_day_confirmation_keyboard()
    )


# Обработка выполнения задания
@router.callback_query(F.data == "day_completed")
async def day_completed(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return

    current_day = user[4]

    if current_day > 30:
        await callback.answer("Вы уже завершили 30-дневную программу!")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO progress (user_id, day, completed, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, current_day, True, timestamp)
    )

    # Увеличиваем текущий день пользователя
    new_day = current_day + 1
    cursor.execute(
        "UPDATE users SET current_day = ? WHERE user_id = ?",
        (new_day, user_id)
    )
    conn.commit()

    await callback.answer("Отлично! Задание выполнено. 👍")
    await callback.message.answer("Прекрасная работа!🚀")

    # Отправляем задание следующего дня
    await send_day_task(user_id, new_day)


# Остальные обработчики остаются без изменений
@router.message(F.text == "📅 Сегодняшнее задание")
async def today_task(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT current_day FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result:
        await message.answer("Пожалуйста, начните с команды /start")
        return
    current_day = result[0]
    if current_day > 30:
        await message.answer("Поздравляю! Вы завершили 30-дневный марафон! 🎉")
        return
    await send_day_task(user_id, current_day)


@router.message(F.text == "ℹ️ О проекте")
async def about(message: types.Message):
    await message.answer(
        "ℹ️ О проекте:\n\n"
        "Это 30-дневный марафон по снижению зависимости от социальных сетей.\n\n"
        "Каждый день ты будешь получать небольшое задание, которое поможет тебе:\n"
        "🔹 Осознать свои привычки\n"
        "🔹 Сократить время в соцсетях\n"
        "🔹 Найти более полезные занятия\n"
        "🔹 Улучшить качество жизни\n\n"
        "Начни с команды /start или продолжи с текущего дня!"
    )


@router.message(F.text == "📊 Мой прогресс")
async def my_progress(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("""
        SELECT u.current_day, COUNT(p.id) as completed_days
        FROM users u
        LEFT JOIN progress p ON u.user_id = p.user_id AND p.completed = 1
        WHERE u.user_id = ?
        GROUP BY u.user_id
    """, (user_id,))
    result = cursor.fetchone()
    if not result:
        await message.answer("Пожалуйста, начните с команды /start")
        return
    current_day, completed_days = result
    if current_day > 30:
        progress_percent = 100
        days_left = 0
    else:
        progress_percent = int((current_day - 1) / 30 * 100)
        days_left = 30 - (current_day - 1)
    total_saved_hours = completed_days * 1
    await message.answer(
        f"📊 Твой прогресс:\n\n"
        f"🔹 Пройдено дней: {current_day - 1} из 30 ({progress_percent}%)\n"
        f"🔹 Осталось дней: {days_left}\n"
        f"🔹 Выполнено заданий: {completed_days}\n"
        f"🔹 Примерно сэкономлено времени: {total_saved_hours} часов\n\n"
        "Продолжай в том же духе! Каждый день приближает тебя к цели. 💪"
    )
