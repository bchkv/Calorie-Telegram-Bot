import asyncio
import os
from pathlib import Path
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    BotCommand,
    ErrorEvent,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from dotenv import load_dotenv

from vision import estimate_meal, estimate_text_meal
from db import (
    add_meal,
    get_today_totals,
    get_today_meals,
    get_totals_for_day,
    get_meal_count_for_day,
    get_nutrition_day,
    get_meal_by_id,
    delete_meal,
    set_daily_goal,
    get_daily_goal,
    get_daily_history,
    get_average_stats,
    get_calorie_extremes,
)
from ui import (
    format_meal,
    format_today_totals,
    format_today_meals,
    format_goal,
    format_goal_set,
    format_stats,
)

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


def meal_actions_keyboard(meal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Today", callback_data="show_today"),
                InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_meal:{meal_id}"),
            ]
        ]
    )


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="today", description="Show today's meals"),
        BotCommand(command="delete", description="Delete a meal: /delete <number>"),
        BotCommand(command="goal", description="Set daily calorie & protein goal"),
        BotCommand(command="help", description="How to use the bot"),
        BotCommand(command="stats", description="Show long-term stats"),
    ]
    await bot.set_my_commands(commands)


@dp.errors()
async def error_handler(event: ErrorEvent):
    logger.exception("Unhandled error: %s", event.exception)


async def save_meal_and_reply(message: Message, result: dict):
    user_id = message.from_user.id
    dt = message.date
    nutrition_day = get_nutrition_day(user_id, dt)

    meal_id = add_meal(
        user_id,
        result["dish"],
        result["calories"],
        result["protein"],
        dt,
    )

    meal_number = get_meal_count_for_day(user_id, nutrition_day)
    totals = get_totals_for_day(user_id, nutrition_day)
    goal = get_daily_goal(user_id)

    meal_text = format_meal(
        meal_number,
        result["dish"],
        result["calories"],
        result["protein"],
    )
    totals_text = format_today_totals(totals, goal)

    await message.answer(
        f"{meal_text}\n{totals_text}",
        parse_mode="Markdown",
        reply_markup=meal_actions_keyboard(meal_id),
    )


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Bot is alive. Send me a photo or text description of your meal!")


@dp.message(lambda message: message.photo)
async def photo_handler(message: Message):
    photo = message.photo[-1]
    file_path = TEMP_DIR / f"{photo.file_id}.jpg"

    try:
        file = await bot.get_file(photo.file_id)
        await bot.download_file(file.file_path, destination=file_path)
        result = await estimate_meal(str(file_path), message.caption)
    except Exception:
        logger.exception("Vision processing failed")
        await message.answer("Sorry, I couldn't analyze that meal.")
        return
    finally:
        if file_path.exists():
            os.remove(file_path)

    await save_meal_and_reply(message, result)


@dp.message(lambda m: m.text and not m.text.startswith("/"))
async def text_meal_handler(message: Message):
    try:
        result = await estimate_text_meal(message.text)
    except Exception:
        logger.exception("Text estimation failed")
        await message.answer("Sorry, the meal estimation failed.")
        return

    await save_meal_and_reply(message, result)


@dp.callback_query(lambda c: c.data == "show_today")
async def show_today_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    meals = get_today_meals(user_id)
    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)

    text = format_today_meals(meals, totals, goal)
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("delete_meal:"))
async def delete_meal_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    try:
        meal_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("Invalid delete action.", show_alert=True)
        return

    meal = get_meal_by_id(meal_id)
    if not meal:
        await callback.answer("Meal already deleted.", show_alert=True)
        return

    if meal["user_id"] != user_id:
        await callback.answer("You cannot delete this meal.", show_alert=True)
        return

    delete_meal(meal_id)

    totals = get_totals_for_day(user_id, meal["nutrition_day"])
    goal = get_daily_goal(user_id)
    totals_text = format_today_totals(totals, goal)

    await callback.message.edit_text(
        f"❌ Deleted: *{meal['dish']}*\n\n{totals_text}",
        parse_mode="Markdown",
    )
    await callback.answer("Meal deleted.")


@dp.message(Command("delete"))
async def delete_meal_handler(message: Message):
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
async def today_handler(message: Message):
    user_id = message.from_user.id
    meals = get_today_meals(user_id)
    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)

    text = format_today_meals(meals, totals, goal)
    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("goal"))
async def goal_handler(message: Message):
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


@dp.message(Command("stats"))
async def stats_handler(message: Message):
    user_id = message.from_user.id

    avg_7 = get_average_stats(user_id, days=7)
    history = get_daily_history(user_id, limit=7)
    extremes = get_calorie_extremes(user_id)

    text = format_stats(avg_7, history, extremes)
    await message.answer(text, parse_mode="Markdown")


async def main():
    logger.info("Bot starting...")
    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())