import sqlite3
from datetime import datetime, date

DB_PATH = "meals.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
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

    conn.commit()
    conn.close()


def add_meal(user_id: int, dish: str, calories: int, protein: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO meals (user_id, dish, calories, protein, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, dish, calories, protein, datetime.utcnow().isoformat())
    )

    conn.commit()
    conn.close()


def get_today_totals(user_id: int):
    conn = sqlite3.connect(DB_PATH)
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

    conn.close()

    return {
        "calories": calories,
        "protein": protein
    }


# initialize DB when module loads
init_db()