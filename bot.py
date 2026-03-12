import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, ErrorEvent, Message
from dotenv import load_dotenv

from db import (
    add_meal,
    delete_meal,
    get_daily_goal,
    get_today_meal_count,
    get_today_meals,
    get_today_totals,
    set_daily_goal,
)
from meal_canonicalizer import canonicalize_from_image, canonicalize_from_text
from nutrition_estimation import estimate_nutrition_from_canonical
from ui import format_goal, format_goal_set, format_meal, format_today_meals, format_today_totals

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
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


async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="today", description="Show today's meals"),
        BotCommand(command="delete", description="Delete a meal: /delete <number>"),
        BotCommand(command="goal", description="Set daily calorie & protein goal"),
        BotCommand(command="help", description="How to use the bot"),
    ]
    await bot.set_my_commands(commands)


@dp.errors()
async def error_handler(event: ErrorEvent) -> None:
    logger.exception("Unhandled error: %s", event.exception)


@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer("Bot is alive. Send me a photo or text description of your meal!")


@dp.message(lambda message: message.photo)
async def photo_handler(message: Message) -> None:
    if not message.from_user:
        return

    user_id = message.from_user.id
    photo = message.photo[-1]
    file_path = TEMP_DIR / f"{photo.file_id}.jpg"

    try:
        file = await bot.get_file(photo.file_id)
        await bot.download_file(file.file_path, destination=file_path)

        meal = await canonicalize_from_image(str(file_path), message.caption)
        result = await estimate_nutrition_from_canonical(meal)

    except Exception:
        logger.exception("Photo meal pipeline failed")
        await message.answer("Sorry, I couldn't analyze that meal.")
        return
    finally:
        if file_path.exists():
            file_path.unlink()

    meal_number = get_today_meal_count(user_id) + 1
    add_meal(user_id, result["dish"], result["calories"], result["protein"])

    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)

    meal_text = format_meal(meal_number, result["dish"], result["calories"], result["protein"])
    today_text = format_today_totals(totals, goal)

    await message.answer(f"{meal_text}\n{today_text}", parse_mode="Markdown")


@dp.message(lambda m: m.text and not m.text.startswith("/"))
async def text_meal_handler(message: Message) -> None:
    if not message.from_user or not message.text:
        return

    user_id = message.from_user.id

    try:
        meal = await canonicalize_from_text(message.text)
        result = await estimate_nutrition_from_canonical(meal)
    except Exception:
        logger.exception("Text meal pipeline failed")
        await message.answer("Sorry, the meal estimation failed.")
        return

    meal_number = get_today_meal_count(user_id) + 1
    add_meal(user_id, result["dish"], result["calories"], result["protein"])

    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)

    meal_text = format_meal(meal_number, result["dish"], result["calories"], result["protein"])
    today_text = format_today_totals(totals, goal)

    await message.answer(f"{meal_text}\n{today_text}", parse_mode="Markdown")


@dp.message(Command("delete"))
async def delete_meal_handler(message: Message) -> None:
    if not message.from_user or not message.text:
        return

    user_id = message.from_user.id
    parts = message.text.split()

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Usage: /delete <number>")
        return

    meal_number = int(parts[1])
    meals = get_today_meals(user_id)

    if meal_number < 1 or meal_number > len(meals):
        await message.answer("Invalid meal number.")
        return

    meal = meals[meal_number - 1]
    delete_meal(meal["id"])

    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)
    today_text = format_today_totals(totals, goal)

    await message.answer(
        f"❌ Deleted: **{meal_number}. {meal['dish']}**\n\n{today_text}",
        parse_mode="Markdown",
    )


@dp.message(Command("today"))
async def today_handler(message: Message) -> None:
    if not message.from_user:
        return

    user_id = message.from_user.id
    meals = get_today_meals(user_id)
    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)

    text = format_today_meals(meals, totals, goal)
    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("goal"))
async def goal_handler(message: Message) -> None:
    if not message.from_user or not message.text:
        return

    user_id = message.from_user.id
    parts = message.text.split()

    if len(parts) == 1:
        goal = get_daily_goal(user_id)
        await message.answer(format_goal(goal), parse_mode="Markdown")
        return

    if len(parts) != 3 or not (parts[1].isdigit() and parts[2].isdigit()):
        await message.answer("Usage: /goal <calories> <protein>")
        return

    calories, protein = int(parts[1]), int(parts[2])
    set_daily_goal(user_id, calories, protein)
    await message.answer(format_goal_set(calories, protein), parse_mode="Markdown")


@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Send a meal photo or type a meal description.\n\n"
        "Commands:\n"
        "/today — show today's meals\n"
        "/delete <number> — delete a meal\n"
        "/goal <calories> <protein> — set daily goal\n"
        "/goal — show current goal",
        parse_mode="Markdown",
    )


async def main() -> None:
    logger.info("Bot starting...")
    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
