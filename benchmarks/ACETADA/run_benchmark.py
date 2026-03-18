# benchmark/run_benchmark.py

import asyncio
import csv
import json
import random
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vision import estimate_meal


# =========================
# PATHS
# =========================

DATASET_ROOT = Path("/Users/bochkovoy/ACETADA-Dataset")
DATASET_CSV = DATASET_ROOT / "derived" / "ACETADA-HF-dataset.enriched.csv"

BENCHMARK_DIR = Path(__file__).resolve().parent
RESULTS_CSV = BENCHMARK_DIR / "results.csv"
SUMMARY_JSON = BENCHMARK_DIR / "summary.json"


# =========================
# SETTINGS
# =========================

MAX_ROWS = 150
RANDOM_SAMPLE = True
RANDOM_SEED = 431248142135
MIN_CONSUMED_RATIO = 0.95


FIELDNAMES = [
    "run_timestamp",
    "meal_index",
    "participant_id",
    "meal_type",
    "food_item_count",
    "cleaned_total_consumed_g",
    "cleaned_total_portion_g",
    "consumed_ratio",
    "groundtruth_items",
    "groundtruth_item_count_check",
    "image_path",
    "pred_dish",
    "pred_calories",
    "pred_protein",
    "true_calories",
    "true_protein",
    "calorie_error",
    "protein_error",
    "calorie_abs_error",
    "protein_abs_error",
    "calorie_pct_error",
    "protein_pct_error",
    "status",
    "error_message",
]


# =========================
# HELPERS
# =========================

def ensure_output_files_ready() -> None:
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()


def append_result(result: dict) -> None:
    with RESULTS_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(result)


def write_summary(summary: dict) -> None:
    with SUMMARY_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def load_dataset_rows() -> list[dict]:
    with DATASET_CSV.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def safe_float(value) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() == "true"


def maybe_sample_rows(rows: list[dict]) -> list[dict]:
    rows = rows.copy()

    if RANDOM_SAMPLE:
        rng = random.Random(RANDOM_SEED)
        rng.shuffle(rows)

    if MAX_ROWS is not None:
        rows = rows[:MAX_ROWS]

    return rows


def filter_rows(rows: list[dict]) -> list[dict]:
    filtered = []

    for row in rows:
        consumed_ratio = safe_float(row.get("consumed_ratio"))
        consumed_ratio_valid = safe_bool(row.get("consumed_ratio_valid"))
        invalid_item_count = safe_float(row.get("invalid_item_count"))

        if not consumed_ratio_valid:
            continue
        if consumed_ratio is None or consumed_ratio <= MIN_CONSUMED_RATIO:
            continue
        if invalid_item_count is None or invalid_item_count != 0:
            continue

        filtered.append(row)

    return filtered


def round_or_none(value: float | None, ndigits: int = 3) -> float | None:
    if value is None:
        return None
    return round(value, ndigits)


def build_before_image_path(row: dict) -> Path:
    return DATASET_ROOT / row["before_filepath"]


def get_ground_truth(row: dict) -> tuple[float | None, float | None]:
    true_calories = safe_float(row.get("cleaned_total_kcal"))
    true_protein = safe_float(row.get("cleaned_total_protein_g"))
    return true_calories, true_protein


def get_portion_totals(row: dict) -> tuple[float | None, float | None, float | None]:
    total_consumed_g = safe_float(row.get("cleaned_total_consumed_g"))
    total_portion_g = safe_float(row.get("cleaned_total_portion_g"))
    consumed_ratio = safe_float(row.get("consumed_ratio"))
    return total_consumed_g, total_portion_g, consumed_ratio


def compute_error(pred: float | None, true: float | None) -> tuple[float | None, float | None]:
    if pred is None or true is None:
        return None, None

    signed_error = pred - true
    abs_error = abs(signed_error)
    return signed_error, abs_error


def compute_pct_error(abs_error: float | None, true: float | None) -> float | None:
    if abs_error is None or true is None or true == 0:
        return None
    return abs_error / true


def extract_groundtruth_items(row: dict) -> list[str]:
    items = []

    for i in range(1, 16):
        name = row.get(f"food_item_{i}_name")
        if name is not None:
            name = name.strip()

        if name:
            items.append(name)

    return items


def format_groundtruth_items(items: list[str]) -> str:
    return " | ".join(items)


def build_summary(
    *,
    total_rows: int,
    count_ok: int,
    count_failed: int,
    count_calorie: int,
    count_protein: int,
    sum_abs_calorie_error: float,
    sum_abs_protein_error: float,
    cumulative_calorie_error: float,
    cumulative_protein_error: float,
    total_true_calories: float,
    total_pred_calories: float,
) -> dict:
    final_mae_calories = round_or_none(sum_abs_calorie_error / count_calorie) if count_calorie else None
    final_mae_protein = round_or_none(sum_abs_protein_error / count_protein) if count_protein else None

    final_cumulative_calorie_error = round_or_none(cumulative_calorie_error)
    final_cumulative_protein_error = round_or_none(cumulative_protein_error)

    final_total_true_calories = round_or_none(total_true_calories)
    final_total_pred_calories = round_or_none(total_pred_calories)

    final_total_calorie_error = round_or_none(total_pred_calories - total_true_calories)

    final_relative_total_calorie_error = None
    if total_true_calories != 0:
        final_relative_total_calorie_error = round_or_none(
            (total_pred_calories - total_true_calories) / total_true_calories
        )

    final_mean_signed_calorie_error = round_or_none(cumulative_calorie_error / count_calorie) if count_calorie else None
    final_mean_signed_protein_error = round_or_none(cumulative_protein_error / count_protein) if count_protein else None

    return {
        "run_timestamp": datetime.now().isoformat(timespec="seconds"),
        "dataset_csv": str(DATASET_CSV),
        "dataset_root": str(DATASET_ROOT),
        "results_csv": str(RESULTS_CSV),
        "max_rows": MAX_ROWS,
        "random_sample": RANDOM_SAMPLE,
        "random_seed": RANDOM_SEED,
        "min_consumed_ratio": MIN_CONSUMED_RATIO,
        "rows_total": total_rows,
        "rows_ok": count_ok,
        "rows_failed": count_failed,
        "rows_with_calorie_prediction": count_calorie,
        "rows_with_protein_prediction": count_protein,
        "final_mae_calories": final_mae_calories,
        "final_mae_protein": final_mae_protein,
        "final_cumulative_calorie_error": final_cumulative_calorie_error,
        "final_cumulative_protein_error": final_cumulative_protein_error,
        "final_mean_signed_calorie_error": final_mean_signed_calorie_error,
        "final_mean_signed_protein_error": final_mean_signed_protein_error,
        "final_total_true_calories": final_total_true_calories,
        "final_total_pred_calories": final_total_pred_calories,
        "final_total_calorie_error": final_total_calorie_error,
        "final_relative_total_calorie_error": final_relative_total_calorie_error,
    }


# =========================
# CORE
# =========================

async def benchmark_one_meal(row: dict, meal_index: int) -> dict:
    participant_id = row.get("participant_id")
    meal_type = row.get("meal_type")
    food_item_count = row.get("food_item_count")

    groundtruth_items = extract_groundtruth_items(row)
    groundtruth_items_str = format_groundtruth_items(groundtruth_items)

    image_path = build_before_image_path(row)
    true_calories, true_protein = get_ground_truth(row)
    total_consumed_g, total_portion_g, consumed_ratio = get_portion_totals(row)

    result = {
        "run_timestamp": datetime.now().isoformat(timespec="seconds"),
        "meal_index": meal_index,
        "participant_id": participant_id,
        "meal_type": meal_type,
        "food_item_count": food_item_count,
        "cleaned_total_consumed_g": round_or_none(total_consumed_g),
        "cleaned_total_portion_g": round_or_none(total_portion_g),
        "consumed_ratio": round_or_none(consumed_ratio),
        "groundtruth_items": groundtruth_items_str,
        "groundtruth_item_count_check": len(groundtruth_items),
        "image_path": str(image_path),
        "pred_dish": None,
        "pred_calories": None,
        "pred_protein": None,
        "true_calories": round_or_none(true_calories),
        "true_protein": round_or_none(true_protein),
        "calorie_error": None,
        "protein_error": None,
        "calorie_abs_error": None,
        "protein_abs_error": None,
        "calorie_pct_error": None,
        "protein_pct_error": None,
        "status": "pending",
        "error_message": None,
    }

    if not image_path.exists():
        result["status"] = "failed"
        result["error_message"] = "image file not found"
        return result

    try:
        prediction = await estimate_meal(str(image_path))

        pred_dish = prediction.get("dish")
        pred_calories = safe_float(prediction.get("calories"))
        pred_protein = safe_float(prediction.get("protein"))

        calorie_error, calorie_abs_error = compute_error(pred_calories, true_calories)
        protein_error, protein_abs_error = compute_error(pred_protein, true_protein)

        calorie_pct_error = compute_pct_error(calorie_abs_error, true_calories)
        protein_pct_error = compute_pct_error(protein_abs_error, true_protein)

        result["pred_dish"] = pred_dish
        result["pred_calories"] = round_or_none(pred_calories)
        result["pred_protein"] = round_or_none(pred_protein)

        result["calorie_error"] = round_or_none(calorie_error)
        result["protein_error"] = round_or_none(protein_error)
        result["calorie_abs_error"] = round_or_none(calorie_abs_error)
        result["protein_abs_error"] = round_or_none(protein_abs_error)
        result["calorie_pct_error"] = round_or_none(calorie_pct_error)
        result["protein_pct_error"] = round_or_none(protein_pct_error)

        result["status"] = "ok"
        return result

    except Exception as e:
        result["status"] = "failed"
        result["error_message"] = str(e)
        return result


async def main() -> None:
    ensure_output_files_ready()

    rows = load_dataset_rows()
    rows = filter_rows(rows)
    rows = maybe_sample_rows(rows)

    total_rows = len(rows)

    print(f"Filtered rows selected for benchmark: {total_rows}")

    sum_abs_calorie_error = 0.0
    sum_abs_protein_error = 0.0
    count_calorie = 0
    count_protein = 0

    cumulative_calorie_error = 0.0
    cumulative_protein_error = 0.0

    total_true_calories = 0.0
    total_pred_calories = 0.0

    count_ok = 0
    count_failed = 0

    for meal_index, row in enumerate(rows, start=1):
        result = await benchmark_one_meal(row, meal_index)

        if result["status"] == "ok":
            count_ok += 1
        else:
            count_failed += 1

        if result["calorie_abs_error"] is not None:
            sum_abs_calorie_error += result["calorie_abs_error"]
            count_calorie += 1

        if result["protein_abs_error"] is not None:
            sum_abs_protein_error += result["protein_abs_error"]
            count_protein += 1

        if result["calorie_error"] is not None:
            cumulative_calorie_error += result["calorie_error"]

        if result["protein_error"] is not None:
            cumulative_protein_error += result["protein_error"]

        if result["true_calories"] is not None:
            total_true_calories += result["true_calories"]

        if result["pred_calories"] is not None:
            total_pred_calories += result["pred_calories"]

        append_result(result)

        print(
            f"[{meal_index}/{total_rows}] "
            f"{result['status']} | "
            f"{Path(result['image_path']).name} | "
            f"kcal_err={result['calorie_error']} | "
            f"protein_err={result['protein_error']}"
        )

    summary = build_summary(
        total_rows=total_rows,
        count_ok=count_ok,
        count_failed=count_failed,
        count_calorie=count_calorie,
        count_protein=count_protein,
        sum_abs_calorie_error=sum_abs_calorie_error,
        sum_abs_protein_error=sum_abs_protein_error,
        cumulative_calorie_error=cumulative_calorie_error,
        cumulative_protein_error=cumulative_protein_error,
        total_true_calories=total_true_calories,
        total_pred_calories=total_pred_calories,
    )
    write_summary(summary)

    print("Done.")
    print(f"Results: {RESULTS_CSV}")
    print(f"Summary: {SUMMARY_JSON}")


if __name__ == "__main__":
    asyncio.run(main())