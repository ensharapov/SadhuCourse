import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database
import scheduler

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")  # URL to GitHub Pages

if not TOKEN:
    print("Error: BOT_TOKEN is not set in .env")
    # We allow running for code generation purposes, but it won't connect
    # sys.exit(1)

dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await database.add_user(
        message.from_user.id, 
        message.from_user.username, 
        message.from_user.full_name
    )
    
    # Create keyboard with WebApp button
    builder = InlineKeyboardBuilder()
    if WEBAPP_URL:
        builder.button(text="🔥 Открыть Практику", web_app=WebAppInfo(url=WEBAPP_URL))
    else:
        builder.button(text="🔥 Открыть Практику (Demo)", callback_data="demo_mode")
        
    await message.answer(
        f"Привет, {message.from_user.first_name}! Rad видеть тебя на пути Садху.\n\n"
        "Нажми кнопку ниже, чтобы записаться на ближайший открытый вебинар и узнать силу гвоздей.",
        reply_markup=builder.as_markup()
    )

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    """
    Handles data sent from the Mini App (via sendData).
    Expected data: JSON string from frontend.
    """
    data = message.web_app_data.data
    # We expect something like {"action": "register_webinar", "status": "confirmed"}
    
    if "register_webinar" in data:
        await database.set_webinar_registration(message.from_user.id)
        await message.answer(
            "✅ Отлично! Вы записаны на вебинар.\n"
            "Я напомню вам о начале за 1 час."
        )

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Initialize DB
    await database.init_db()
    
    # Initialize Bot
    if TOKEN:
        bot = Bot(token=TOKEN)
        # Setup Scheduler
        scheduler.setup_scheduler(bot)
        
        await dp.start_polling(bot)
    else:
        logging.warning("BOT_TOKEN not found. Bot will not start polling.")

if __name__ == "__main__":
    asyncio.run(main())
