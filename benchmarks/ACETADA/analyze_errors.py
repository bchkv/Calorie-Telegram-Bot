# benchmark/analyze_errors.py

import pandas as pd
from pathlib import Path


RESULTS_CSV = Path(__file__).resolve().parent / "results.csv"

SHOW_N = 25

COLUMNS_TO_SHOW = [
    "groundtruth_items",
    "pred_dish",
    "true_calories",
    "pred_calories",
    "calorie_error",
    "true_protein",
    "pred_protein",
    "protein_error",
    "meal_type",
    "food_item_count",
]


def load_results() -> pd.DataFrame:
    return pd.read_csv(RESULTS_CSV)


def show_overall_summary(df: pd.DataFrame) -> None:
    ok = df[df["status"] == "ok"].copy()

    if ok.empty:
        print("No successful rows found.")
        return

    mae_calories = ok["calorie_abs_error"].mean()
    mae_protein = ok["protein_abs_error"].mean()
    mean_calorie_error = ok["calorie_error"].mean()
    mean_protein_error = ok["protein_error"].mean()

    total_true_calories = ok["true_calories"].sum()
    total_pred_calories = ok["pred_calories"].sum()
    total_calorie_error = total_pred_calories - total_true_calories
    relative_total_calorie_error = (
        total_calorie_error / total_true_calories if total_true_calories else None
    )

    print("=== OVERALL SUMMARY ===")
    print(f"Rows (ok): {len(ok)}")
    print(f"MAE calories: {mae_calories:.3f}")
    print(f"MAE protein: {mae_protein:.3f}")
    print(f"Mean calorie error: {mean_calorie_error:.3f}")
    print(f"Mean protein error: {mean_protein_error:.3f}")
    print(f"Total true calories: {total_true_calories:.3f}")
    print(f"Total predicted calories: {total_pred_calories:.3f}")
    print(f"Total calorie error: {total_calorie_error:.3f}")
    if relative_total_calorie_error is not None:
        print(f"Relative total calorie error: {relative_total_calorie_error:.3%}")
    print()


def show_worst_cases(df: pd.DataFrame, n: int = SHOW_N) -> None:
    ok = df[df["status"] == "ok"].copy()
    worst = ok.sort_values("calorie_error", ascending=True).head(n)

    print(f"=== WORST {n} CASES (MOST NEGATIVE CALORIE ERROR) ===")
    if worst.empty:
        print("No rows found.\n")
        return

    print(worst[COLUMNS_TO_SHOW].to_string(index=False))
    print()


def show_best_cases(df: pd.DataFrame, n: int = SHOW_N) -> None:
    ok = df[df["status"] == "ok"].copy()
    best = ok.sort_values("calorie_error", ascending=False).head(n)

    print(f"=== BEST {n} CASES (MOST POSITIVE CALORIE ERROR) ===")
    if best.empty:
        print("No rows found.\n")
        return

    print(best[COLUMNS_TO_SHOW].to_string(index=False))
    print()


def show_by_meal_type(df: pd.DataFrame) -> None:
    ok = df[df["status"] == "ok"].copy()

    if ok.empty:
        return

    summary = (
        ok.groupby("meal_type", dropna=False)
        .agg(
            rows=("meal_type", "size"),
            mean_calorie_error=("calorie_error", "mean"),
            mae_calories=("calorie_abs_error", "mean"),
            mean_protein_error=("protein_error", "mean"),
            mae_protein=("protein_abs_error", "mean"),
        )
        .sort_values("mae_calories", ascending=False)
    )

    print("=== BY MEAL TYPE ===")
    print(summary.to_string())
    print()


def show_by_item_count(df: pd.DataFrame) -> None:
    ok = df[df["status"] == "ok"].copy()

    if ok.empty:
        return

    summary = (
        ok.groupby("food_item_count", dropna=False)
        .agg(
            rows=("food_item_count", "size"),
            mean_calorie_error=("calorie_error", "mean"),
            mae_calories=("calorie_abs_error", "mean"),
            mean_protein_error=("protein_error", "mean"),
            mae_protein=("protein_abs_error", "mean"),
        )
        .sort_values("food_item_count")
    )

    print("=== BY FOOD ITEM COUNT ===")
    print(summary.to_string())
    print()


def main() -> None:
    df = load_results()
    show_overall_summary(df)
    show_worst_cases(df)
    show_best_cases(df)
    show_by_meal_type(df)
    show_by_item_count(df)


if __name__ == "__main__":
    main()