import asyncio
from aiogram import Dispatcher
from dotenv import load_dotenv
from app.handlers import router


async def main():
    load_dotenv()
    from config import bot

    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
