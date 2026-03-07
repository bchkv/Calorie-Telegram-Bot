import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Bot is alive.")


# Stage 2 — photo handler
@dp.message(lambda message: message.photo)
async def photo_handler(message: Message):

    caption = message.caption

    # log caption to console
    print("Photo received")
    print("Caption:", caption)

    if caption:
        await message.answer(f"got photo\ncaption: {caption}")
    else:
        await message.answer("got photo")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
