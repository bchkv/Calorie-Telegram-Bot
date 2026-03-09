from db import get_today_totals, get_daily_goal


def format_today_totals(user_id: int) -> str:
    totals = get_today_totals(user_id)
    goal = get_daily_goal(user_id)

    if goal:
        calories_line = f"🔥 *{totals['calories']} / {goal['calories']} kcal*"
        protein_line = f"💪 *{totals['protein']} / {goal['protein']} g protein*"
    else:
        calories_line = f"🔥 *{totals['calories']} kcal*"
        protein_line = f"💪 *{totals['protein']} g protein*"

    return (
        "────────────\n"
        "📊 *Today*\n\n"
        f"{calories_line}\n"
        f"{protein_line}"
    )

def format_today_meals(meals: list, totals: dict, goal: dict | None) -> str:

    lines = ["📊 *Today meals:*\n"]

    for i, meal in enumerate(meals, start=1):
        lines.append(
            f"*#{i}* 🍽 {meal['dish']} — "
            f"{meal['calories']} kcal • {meal['protein']} g protein"
        )

    lines.append("\n────────────\n")

    if goal:
        lines.append(
            f"🔥 *{totals['calories']} / {goal['calories']} kcal*\n"
            f"💪 *{totals['protein']} / {goal['protein']} g protein*"
        )
    else:
        lines.append(
            f"🔥 *{totals['calories']} kcal*\n"
            f"💪 *{totals['protein']} g protein*"
        )

    return "\n".join(lines)


def format_goal(goal: dict | None) -> str:

    if goal:
        return (
            f"🎯 *Your current goal*\n\n"
            f"🔥 {goal['calories']} kcal\n"
            f"💪 {goal['protein']} g protein\n\n"
            f"To change:\n"
            f"`/goal calories protein`\n"
            f"Example: `/goal 2500 150`"
        )

    return (
        "🎯 *Set your daily goal*\n\n"
        "Usage:\n"
        "`/goal calories protein`\n\n"
        "Example:\n"
        "`/goal 2500 150`"
    )


def format_goal_set(calories: int, protein: int) -> str:
    return (
        f"🎯 *Daily goal set*\n\n"
        f"🔥 {calories} kcal\n"
        f"💪 {protein} g protein"
    )


def format_meal(meal_number: int, dish: str, calories: float, protein: float) -> str:
    return (
        f"*#{meal_number} 🍽 {dish}*\n\n"
        f"🔥 *{calories} kcal*\n"
        f"💪 *{protein} g protein*"
    )


def format_today_totals(totals: dict, goal: dict | None) -> str:
    if goal:
        calories = f"🔥 *{totals['calories']} / {goal['calories']} kcal*"
        protein = f"💪 *{totals['protein']} / {goal['protein']} g protein*"
    else:
        calories = f"🔥 *{totals['calories']} kcal*"
        protein = f"💪 *{totals['protein']} g protein*"

    return (
        "────────────\n"
        "📊 *Today*\n\n"
        f"{calories}\n"
        f"{protein}"
    )


def format_today_list(meals: list, totals: dict, goal: dict | None) -> str:

    lines = ["📊 *Today meals:*\n"]

    for i, meal in enumerate(meals, start=1):
        lines.append(
            f"*#{i}* 🍽 {meal['dish']} — "
            f"{meal['calories']} kcal • {meal['protein']} g protein"
        )

    lines.append("\n" + format_today_totals(totals, goal))

    return "\n".join(lines)