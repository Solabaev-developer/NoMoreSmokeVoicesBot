# bot/main.py
import asyncio
import asyncpg
from aiogram import Bot, Dispatcher
from handlers import router  # ваш основной router
import handlers as handlers   # чтобы записать в handlers.db
from aiogram.types import InlineQuery, InlineQueryResultVoice
import os

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp  = Dispatcher()

    db = await asyncpg.connect(os.getenv("POSTGRES_DSN"))
    handlers.db = db                 # сохраняем соединение

    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())