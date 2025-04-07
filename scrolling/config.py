from aiogram import Bot
from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

# Получаем токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Токен бота не найден в .env!")

# Создаем и возвращаем объект бота
bot = Bot(token=BOT_TOKEN)
