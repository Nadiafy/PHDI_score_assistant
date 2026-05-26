import asyncio
from aiogram import Bot, Dispatcher
from tg_bot_test import dp
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=TOKEN)

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
