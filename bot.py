import asyncio
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from dotenv import load_dotenv

from vision import estimate_meal
from db import add_meal, get_today_totals

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

    print("Photo received")
    print("Caption:", caption)

    # get file info from Telegram
    file = await bot.get_file(photo.file_id)

    # choose local path
    file_path = TEMP_DIR / f"{photo.file_id}.jpg"

    # download the file
    await bot.download_file(file.file_path, destination=file_path)

    print("Saved photo to:", file_path)

    result = estimate_meal(str(file_path), caption)

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