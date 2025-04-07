from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


buttons = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Сегодняшнее задание"), KeyboardButton(text="📊 Мой прогресс")],
        [KeyboardButton(text="ℹ️ О проекте")]
    ],
    resize_keyboard=True
)
