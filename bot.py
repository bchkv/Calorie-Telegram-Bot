import asyncio
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand

from dotenv import load_dotenv

from vision import estimate_meal, estimate_text_meal
from db import (add_meal, get_today_totals, get_today_meal_count, get_today_meals, delete_meal, set_daily_goal,
                get_daily_goal)
from ui import format_meal, format_today_totals, format_today_list, format_today_meals, format_goal, format_goal_set

from aiogram.types import ErrorEvent

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
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

async def set_commands(bot: Bot):

    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="today", description="Show today's meals"),
        BotCommand(command="delete", description="Delete a meal: /delete <number>"),
        BotCommand(command="goal", description="Set daily calorie & protein goal"),
        BotCommand(command="help", description="How to use the bot"),
    ]

    await bot.set_my_commands(commands)

@dp.errors()
async def error_handler(event: ErrorEvent):
    logger.exception("Unhandled error: %s", event.exception)


@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"
    logger.info("User %s [%s] start command", user_id, username)
    await message.answer("Bot is alive.")

@dp.message(lambda message: message.photo)
async def photo_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    caption = message.caption
    photo = message.photo[-1]

    logger.info("User %s [%s] sent photo", user_id, username)
    logger.info("Caption: %s", caption)

    file_path = TEMP_DIR / f"{photo.file_id}.jpg"

    try:
        file = await bot.get_file(photo.file_id)
        await bot.download_file(file.file_path, destination=file_path)
    except Exception:
        logger.exception("Photo download failed for user %s [%s]", user_id, username)
        await message.answer("Failed to download the photo.")
        return

    logger.info("Saved photo to %s", file_path)

    try:
        result = await estimate_meal(str(file_path), caption)
    except Exception:
        logger.exception("Vision estimation failed for user %s [%s]", user_id, username)
        await message.answer("Sorry, I couldn't analyze that meal.")
        return
    finally:
        if file_path.exists():
            os.remove(file_path)

    meal_number = get_today_meal_count(user_id) + 1

    add_meal(
        user_id,
        result["dish"],
        result["calories"],
        result["protein"]
    )

    logger.info(
        "User %s [%s] meal saved: %s (%s kcal, %s g protein)",
        user_id,
        username,
        result["dish"],
        result["calories"],
        result["protein"],
    )

    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)

    today_text = format_today_totals(totals, goal)

    await message.answer(
        f"*#{meal_number} 🍽 {result['dish']}*\n\n"
        f"🔥 *{result['calories']} kcal*\n"
        f"💪 *{result['protein']} g protein*\n\n"
        f"{today_text}",
        parse_mode="Markdown"
    )

@dp.message(lambda m: m.text and not m.text.startswith("/"))
async def text_meal_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    text = message.text

    logger.info("User %s [%s] text meal: %s", user_id, username, text)

    try:
        result = await estimate_text_meal(text)
    except Exception:
        logger.exception("Text meal estimation failed for user %s [%s]", user_id, username)
        await message.answer("Sorry, the meal estimation failed.")
        return

    meal_number = get_today_meal_count(user_id) + 1

    add_meal(
        user_id,
        result["dish"],
        result["calories"],
        result["protein"]
    )

    logger.info(
        "User %s [%s] meal saved: %s (%s kcal, %s g protein)",
        user_id,
        username,
        result["dish"],
        result["calories"],
        result["protein"],
    )

    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)

    today_text = format_today_totals(totals, goal)

    await message.answer(
        f"*#{meal_number} 🍽 {result['dish']}*\n\n"
        f"🔥 *{result['calories']} kcal*\n"
        f"💪 *{result['protein']} g protein*\n\n"
        f"{today_text}",
        parse_mode="Markdown"
    )

@dp.message(Command("delete"))
async def delete_meal_handler(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    parts = message.text.split()

    if len(parts) != 2:
        await message.answer("Usage: /delete <meal_number>")
        return

    try:
        meal_number = int(parts[1])
    except ValueError:
        await message.answer("Meal number must be an integer.")
        return

    meals = get_today_meals(user_id)

    if meal_number < 1 or meal_number > len(meals):
        await message.answer("Invalid meal number.")
        return

    meal = meals[meal_number - 1]

    delete_meal(meal["id"])

    logger.info(
        "User %s [%s] deleted meal #%s (%s)",
        user_id,
        username,
        meal_number,
        meal["dish"]
    )

    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)

    today_text = format_today_totals(totals, goal)

    await message.answer(
        f"❌ Deleted *#{meal_number} {meal['dish']}*\n\n"
        f"{today_text}",
        parse_mode="Markdown"
    )

@dp.message(Command("today"))
async def today_handler(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    logger.info("User %s [%s] requested /today", user_id, username)

    meals = get_today_meals(user_id)

    if not meals:
        await message.answer("📊 Today\n\nNo meals logged yet.")
        return

    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)

    text = format_today_meals(meals, totals, goal)

    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("goal"))
async def goal_handler(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username or "no_username"

    parts = message.text.split()

    if len(parts) == 1:
        goal = get_daily_goal(user_id)
        await message.answer(format_goal(goal), parse_mode="Markdown")
        return

    if len(parts) != 3:
        await message.answer("Usage: /goal <calories> <protein>")
        return

    try:
        calories = int(parts[1])
        protein = int(parts[2])
    except ValueError:
        await message.answer("Calories and protein must be numbers.")
        return

    set_daily_goal(user_id, calories, protein)

    logger.info(
        "User %s [%s] set daily goal: %s kcal, %s g protein",
        user_id,
        username,
        calories,
        protein
    )

    await message.answer(
        format_goal_set(calories, protein),
        parse_mode="Markdown"
    )

async def main():
    logger.info("Bot starting...")

    await set_commands(bot)

    await dp.start_polling(bot)

if __name__ == "__main__":
        asyncio.run(main())