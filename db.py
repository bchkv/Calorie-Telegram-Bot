import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "meals.db"
DEFAULT_DAY_START_HOUR = 3


def get_nutrition_day(user_id: int, dt: datetime | None = None) -> str:
    """Return the logical nutrition day for a datetime, respecting user's day start hour."""
    if dt is None:
        dt = datetime.utcnow()

    hour = get_day_start_hour(user_id)

    if dt.hour < hour:
        dt = dt - timedelta(days=1)

    return dt.date().isoformat()


def backfill_nutrition_days():
    """Fill nutrition_day for old rows created before this column existed."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, user_id, created_at
                FROM meals
                WHERE nutrition_day IS NULL
            """)
            rows = cursor.fetchall()

            for meal_id, user_id, created_at in rows:
                dt = datetime.fromisoformat(created_at)
                nutrition_day = get_nutrition_day(user_id, dt)

                cursor.execute(
                    "UPDATE meals SET nutrition_day = ? WHERE id = ?",
                    (nutrition_day, meal_id),
                )

        logger.info("Nutrition day backfill complete")

    except Exception:
        logger.exception("Failed to backfill nutrition_day")
        raise


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
            day_start_hour INTEGER DEFAULT 3
        )
        """)

        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN calorie_goal INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE user_settings ADD COLUMN protein_goal INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE meals ADD COLUMN nutrition_day TEXT")
        except sqlite3.OperationalError:
            pass

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_meals_user_created_at
        ON meals(user_id, created_at)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_meals_user_nutrition_day
        ON meals(user_id, nutrition_day)
        """)

    backfill_nutrition_days()
    logger.info("Using database at: %s", DB_PATH)


def get_day_start_hour(user_id: int) -> int:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT day_start_hour FROM user_settings WHERE user_id = ?",
                (user_id,),
            )

            row = cursor.fetchone()

            if row and row[0] is not None:
                return row[0]

            return DEFAULT_DAY_START_HOUR

    except Exception:
        logger.exception("Failed to read user settings for user %s", user_id)
        return DEFAULT_DAY_START_HOUR


def add_meal(
    user_id: int,
    dish: str,
    calories: int,
    protein: int,
    dt: datetime | None = None,
):
    try:
        if dt is None:
            dt = datetime.utcnow()

        nutrition_day = get_nutrition_day(user_id, dt)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO meals (user_id, dish, calories, protein, created_at, nutrition_day)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, dish, calories, protein, dt.isoformat(), nutrition_day),
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
        nutrition_day = get_nutrition_day(user_id)
        return get_totals_for_day(user_id, nutrition_day)
    except Exception:
        logger.exception("Failed to read daily totals for user %s", user_id)
        raise


def get_today_meals(user_id: int):
    """Return today's meals ordered by time."""
    nutrition_day = get_nutrition_day(user_id)
    return get_meals_for_day(user_id, nutrition_day)


def get_meals_for_day(user_id: int, nutrition_day: str):
    """Return meals for a specific nutrition day ordered by time."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, dish, calories, protein, created_at, nutrition_day
            FROM meals
            WHERE user_id = ?
            AND nutrition_day = ?
            ORDER BY created_at ASC
            """,
            (user_id, nutrition_day),
        )

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "dish": row[1],
                "calories": row[2],
                "protein": row[3],
                "created_at": row[4],
                "nutrition_day": row[5],
            }
            for row in rows
        ]


def get_totals_for_day(user_id: int, nutrition_day: str):
    """Return totals for a specific nutrition day."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(calories), 0),
                COALESCE(SUM(protein), 0)
            FROM meals
            WHERE user_id = ?
            AND nutrition_day = ?
            """,
            (user_id, nutrition_day),
        )

        calories, protein = cursor.fetchone()

        return {
            "calories": calories,
            "protein": protein,
        }


def get_meal_count_for_day(user_id: int, nutrition_day: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM meals
            WHERE user_id = ?
            AND nutrition_day = ?
            """,
            (user_id, nutrition_day),
        )

        return cursor.fetchone()[0]


def get_meal_by_id(meal_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, user_id, dish, calories, protein, created_at, nutrition_day
            FROM meals
            WHERE id = ?
            """,
            (meal_id,),
        )

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "user_id": row[1],
            "dish": row[2],
            "calories": row[3],
            "protein": row[4],
            "created_at": row[5],
            "nutrition_day": row[6],
        }


def delete_meal(meal_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM meals WHERE id = ?",
            (meal_id,),
        )


def set_daily_goal(user_id: int, calories: int, protein: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO user_settings (user_id, calorie_goal, protein_goal)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET
                calorie_goal = excluded.calorie_goal,
                protein_goal = excluded.protein_goal
            """,
            (user_id, calories, protein),
        )


def get_daily_goal(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT calorie_goal, protein_goal
            FROM user_settings
            WHERE user_id = ?
            """,
            (user_id,),
        )

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "calories": row[0],
            "protein": row[1],
        }


def get_daily_history(user_id: int, limit: int = 30):
    """Return aggregated daily stats for recent nutrition days."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                nutrition_day,
                COALESCE(SUM(calories), 0) AS calories,
                COALESCE(SUM(protein), 0) AS protein,
                COUNT(*) AS meals_count
            FROM meals
            WHERE user_id = ?
              AND nutrition_day IS NOT NULL
            GROUP BY nutrition_day
            ORDER BY nutrition_day DESC
            LIMIT ?
            """,
            (user_id, limit),
        )

        rows = cursor.fetchall()

    return [
        {
            "day": row[0],
            "calories": row[1],
            "protein": row[2],
            "meals_count": row[3],
        }
        for row in rows
    ]


def get_average_stats(user_id: int, days: int = 7):
    """
    Return average daily calories/protein/meals across the last N nutrition days
    that actually have entries.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT AVG(calories), AVG(protein), AVG(meals_count)
            FROM (
                SELECT
                    nutrition_day,
                    SUM(calories) AS calories,
                    SUM(protein) AS protein,
                    COUNT(*) AS meals_count
                FROM meals
                WHERE user_id = ?
                GROUP BY nutrition_day
                ORDER BY nutrition_day DESC
                LIMIT ?
            )
            """,
            (user_id, days),
        )

        row = cursor.fetchone()

    return {
        "avg_calories": round(row[0] or 0, 1),
        "avg_protein": round(row[1] or 0, 1),
        "avg_meals": round(row[2] or 0, 1),
    }


def get_calorie_extremes(user_id: int):
    """Return the highest- and lowest-calorie nutrition days for the user."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT nutrition_day, SUM(calories) AS total_calories
            FROM meals
            WHERE user_id = ?
              AND nutrition_day IS NOT NULL
            GROUP BY nutrition_day
            ORDER BY total_calories DESC
            LIMIT 1
            """,
            (user_id,),
        )
        max_day = cursor.fetchone()

        cursor.execute(
            """
            SELECT nutrition_day, SUM(calories) AS total_calories
            FROM meals
            WHERE user_id = ?
              AND nutrition_day IS NOT NULL
            GROUP BY nutrition_day
            ORDER BY total_calories ASC
            LIMIT 1
            """,
            (user_id,),
        )
        min_day = cursor.fetchone()

    return {
        "highest": {
            "day": max_day[0],
            "calories": max_day[1],
        } if max_day else None,
        "lowest": {
            "day": min_day[0],
            "calories": min_day[1],
        } if min_day else None,
    }


init_db()