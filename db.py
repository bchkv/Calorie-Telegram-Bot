import sqlite3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

DB_PATH = "meals.db"
DEFAULT_DAY_START_HOUR = 5


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            dish TEXT,
            calories INTEGER,
            protein INTEGER,
            created_at TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            day_start_hour INTEGER DEFAULT 5
        )
        """)


def get_day_start_hour(user_id: int) -> int:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT day_start_hour FROM user_settings WHERE user_id = ?",
                (user_id,)
            )

            row = cursor.fetchone()

            if row:
                return row[0]

            return DEFAULT_DAY_START_HOUR

    except Exception:
        logger.exception("Failed to read user settings for user %s", user_id)
        return DEFAULT_DAY_START_HOUR


def get_day_window(user_id: int):
    """Return start and end timestamps for the user's nutrition day."""
    hour = get_day_start_hour(user_id)

    now = datetime.now()

    start = now.replace(hour=hour, minute=0, second=0, microsecond=0)

    if now.hour < hour:
        start = start - timedelta(days=1)

    end = start + timedelta(days=1)

    return start.isoformat(), end.isoformat()


def add_meal(user_id: int, dish: str, calories: int, protein: int):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO meals (user_id, dish, calories, protein, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, dish, calories, protein, datetime.now().isoformat())
            )

        logger.info(
            "Meal stored for user %s: %s (%s kcal, %s g protein)",
            user_id,
            dish,
            calories,
            protein,
        )

    except Exception:
        logger.exception("Failed to insert meal into database")
        raise


def get_today_totals(user_id: int):
    try:
        start, end = get_day_window(user_id)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(calories), 0),
                    COALESCE(SUM(protein), 0)
                FROM meals
                WHERE user_id = ?
                AND created_at >= ?
                AND created_at < ?
                """,
                (user_id, start, end)
            )

            calories, protein = cursor.fetchone()

            return {
                "calories": calories,
                "protein": protein
            }

    except Exception:
        logger.exception("Failed to read daily totals for user %s", user_id)
        raise


# initialize DB when module loads
init_db()