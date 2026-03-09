import sqlite3
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

DB_PATH = "meals.db"


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


def add_meal(user_id: int, dish: str, calories: int, protein: int):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO meals (user_id, dish, calories, protein, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, dish, calories, protein, datetime.utcnow().isoformat())
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
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            today = date.today().isoformat()

            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(calories), 0),
                    COALESCE(SUM(protein), 0)
                FROM meals
                WHERE user_id = ?
                AND DATE(created_at) = ?
                """,
                (user_id, today)
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