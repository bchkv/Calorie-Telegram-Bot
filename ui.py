from typing import Any

def format_number(value: float) -> str:
    """Removes trailing .0 for integers, otherwise rounds to 1 decimal."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"

def format_meal(meal_number: int, dish: str, calories: float, protein: float) -> str:
    """Individual meal log. Index is bold, everything else is standard."""
    return (
        f"*#{meal_number}* {dish}\n\n"
        f"{format_number(calories)} kcal\n"
        f"{format_number(protein)} g protein"
    )

def format_today_totals(totals: dict, goal: dict | None) -> str:
    """Aligned progress using inline code to avoid the 'copy' block."""
    if not goal:
        return (
            "────────────────────\n"
            f"🔥 {format_number(totals['calories'])} kcal\n"
            f"💪 {format_number(totals['protein'])} g"
        )

    c_diff = goal['calories'] - totals['calories']
    p_diff = goal['protein'] - totals['protein']

    c_status = f"{format_number(c_diff)} left" if c_diff >= 0 else f"{format_number(abs(c_diff))} over"
    p_status = f"{format_number(p_diff)} left" if p_diff >= 0 else f"{format_number(abs(p_diff))} over"

    return (
        "────────────────────\n"
        f"🔥️ `{int(totals['calories']):>5} / {int(goal['calories']):<5} ({c_status})`\n"
        f"💪 `{format_number(totals['protein']):>5} / {format_number(goal['protein']):<5} ({p_status})`"
    )

def format_today_meals(
    meals: list[dict[str, Any]],
    totals: dict[str, Any],
    goal: dict[str, Any] | None,
) -> str:
    """Full list view (Today's Log)."""
    if not meals:
        return "Nothing logged yet today."

    lines = ["📝 *Today's Log*\n"]
    for i, meal in enumerate(meals, start=1):
        lines.append(f"{i}. {meal['dish']} ({format_number(meal['calories'])}k / {format_number(meal['protein'])}p)")

    lines.append(format_today_totals(totals, goal))
    return "\n".join(lines)

def format_goal(goal: dict[str, Any] | None) -> str:
    if goal:
        return (
            "🎯 *Current Goal*\n\n"
            f"🔥 {format_number(goal['calories'])} kcal\n"
            f"💪 {format_number(goal['protein'])} g protein\n\n"
            "To change:\n"
            "`/goal calories protein`"
        )
    return "🎯 *No goal set.*\n\nUse `/goal 2500 150` to set one."

def format_goal_set(calories: int, protein: int) -> str:
    return (
        "🎯 *Daily goal set*\n\n"
        f"🔥 {calories} kcal\n"
        f"💪 {protein} g protein"
    )