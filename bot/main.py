import os
import asyncio
from aiogram import Bot, Dispatcher
from db import init_db
from routers import start_router, new_sticker_router, inline_router, delete_sticker_router, search_by_tags_router

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    await init_db(os.getenv("POSTGRES_DSN"))

    dp.include_router(start_router)
    dp.include_router(new_sticker_router)
    dp.include_router(inline_router)
    dp.include_router(delete_sticker_router)
    dp.include_router(search_by_tags_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
