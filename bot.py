import asyncio
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from dotenv import load_dotenv

from vision import estimate_meal, estimate_text_meal
from db import add_meal, get_today_totals

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)

logger = logging.getLogger(__name__)

load_dotenv(override=True)

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN not set")

bot = Bot(token=TOKEN)
dp = Dispatcher()

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Bot is alive.")


@dp.message(lambda message: message.photo)
async def photo_handler(message: Message):

    caption = message.caption
    photo = message.photo[-1]   # highest resolution

    logger.info("Photo received")
    logger.info("Caption: %s", caption)

    # get file info from Telegram
    file = await bot.get_file(photo.file_id)

    # choose local path
    file_path = TEMP_DIR / f"{photo.file_id}.jpg"

    # download the file
    await bot.download_file(file.file_path, destination=file_path)

    logger.info("Saved photo to %s", file_path)

    result = await estimate_meal(str(file_path), caption)

    # remove the photo after processing
    os.remove(file_path)

    add_meal(
        message.from_user.id,
        result["dish"],
        result["calories"],
        result["protein"]
    )

    totals = get_today_totals(message.from_user.id)

    await message.answer(
        f"{result['dish']}\n"
        f"Calories: {result['calories']} kcal\n"
        f"Protein: {result['protein']} g\n\n"
        f"Today:\n"
        f"Calories: {totals['calories']} kcal\n"
        f"Protein: {totals['protein']} g"
    )

@dp.message(lambda message: message.text)
async def text_meal_handler(message: Message):

    text = message.text

    logger.info("Text meal received: %s", text)

    result = await estimate_text_meal(text)

    add_meal(
        message.from_user.id,
        result["dish"],
        result["calories"],
        result["protein"]
    )

    totals = get_today_totals(message.from_user.id)

    await message.answer(
        f"{result['dish']}\n"
        f"Calories: {result['calories']} kcal\n"
        f"Protein: {result['protein']} g\n\n"
        f"Today:\n"
        f"Calories: {totals['calories']} kcal\n"
        f"Protein: {totals['protein']} g"
    )

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
        asyncio.run(main())