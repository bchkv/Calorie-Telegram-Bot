import asyncio
import csv
import random
import statistics
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from meal_canonicalizer import canonicalize_from_image
from nutrition_estimation import estimate_nutrition_from_canonical


BENCHMARK_LABELS_CSV = Path(
    "/Volumes/T7/Library/nutrition5k_benchmark_dataset_builder/data/labels/labels.csv"
)
BENCHMARK_IMAGES_DIR = Path(
    "/Volumes/T7/Library/nutrition5k_benchmark_dataset_builder/data/processed/frames_selected"
)
RESULTS_CSV = Path(
    "/Volumes/T7/Library/nutrition5k_benchmark_dataset_builder/data/results/benchmark_results.csv"
)

# -----------------------------
# hardcoded benchmark controls
# -----------------------------
MAX_IMAGES = 20          # None = use all images
SHUFFLE_IMAGES = False   # True = randomize image order before limiting
RANDOM_SEED = 42

# -----------------------------
# expected labels.csv columns
# change these if your CSV uses different names
# -----------------------------
DISH_ID_COLUMN = "dish_id"
CALORIES_GT_COLUMN = "calories"
PROTEIN_GT_COLUMN = "protein"

# -----------------------------
# expected prediction keys
# change extract_predictions() if your output schema differs
# -----------------------------


def safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_labels_as_dict(csv_path: Path) -> dict[str, dict]:
    labels_by_dish_id = {}

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            dish_id = str(row[DISH_ID_COLUMN]).strip()

            labels_by_dish_id[dish_id] = {
                "calories_gt": safe_float(row[CALORIES_GT_COLUMN]),
                "protein_gt": safe_float(row[PROTEIN_GT_COLUMN]),
            }

    return labels_by_dish_id


def get_image_paths(images_dir: Path) -> list[Path]:
    image_paths = sorted(images_dir.glob("*.png"))

    if SHUFFLE_IMAGES:
        rng = random.Random(RANDOM_SEED)
        rng.shuffle(image_paths)

    if MAX_IMAGES is not None:
        image_paths = image_paths[:MAX_IMAGES]

    return image_paths


def abs_error(pred: float, gt: float) -> float:
    return abs(pred - gt)


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def median(values: list[float]) -> float:
    return statistics.median(values)


def percent_where(rows: list[dict], predicate) -> float | None:
    if not rows:
        return None
    count = sum(1 for row in rows if predicate(row))
    return 100.0 * count / len(rows)


def extract_predictions(nutrition_result: dict) -> dict[str, float | None]:
    """
    Assumes estimate_nutrition_from_canonical(...) returns something like:
    {
        "calories": ...,
        "protein": ...
    }

    If your real output schema differs, adapt only this function.
    """
    return {
        "calories_pred": safe_float(nutrition_result.get("calories")),
        "protein_pred": safe_float(nutrition_result.get("protein")),
    }


def write_results(results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "dish_id",
        "image_path",
        "calories_gt",
        "protein_gt",
        "calories_pred",
        "protein_pred",
        "calorie_abs_error",
        "protein_abs_error",
        "canonical",
        "nutrition_result",
        "status",
        "error_message",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def compute_summary(results: list[dict]) -> dict:
    ok_rows = [row for row in results if row["status"] == "ok"]

    summary = {
        "n_total": len(results),
        "n_ok": len(ok_rows),
        "n_failed": len(results) - len(ok_rows),
    }

    if not ok_rows:
        return summary

    calorie_errors = [row["calorie_abs_error"] for row in ok_rows]
    protein_errors = [row["protein_abs_error"] for row in ok_rows]

    summary["calorie_mae"] = mean(calorie_errors)
    summary["calorie_median_ae"] = median(calorie_errors)
    summary["protein_mae"] = mean(protein_errors)
    summary["protein_median_ae"] = median(protein_errors)

    summary["calorie_within_50"] = percent_where(
        ok_rows, lambda row: row["calorie_abs_error"] <= 50
    )
    summary["calorie_within_100"] = percent_where(
        ok_rows, lambda row: row["calorie_abs_error"] <= 100
    )
    summary["protein_within_5"] = percent_where(
        ok_rows, lambda row: row["protein_abs_error"] <= 5
    )
    summary["protein_within_10"] = percent_where(
        ok_rows, lambda row: row["protein_abs_error"] <= 10
    )

    return summary


def print_summary(summary: dict) -> None:
    print("\n=== Benchmark summary ===")
    print(f'N total: {summary["n_total"]}')
    print(f'N ok: {summary["n_ok"]}')
    print(f'N failed: {summary["n_failed"]}')

    if summary["n_ok"] == 0:
        return

    print(f'Calories MAE: {summary["calorie_mae"]:.2f} kcal')
    print(f'Calories median AE: {summary["calorie_median_ae"]:.2f} kcal')
    print(f'Protein MAE: {summary["protein_mae"]:.2f} g')
    print(f'Protein median AE: {summary["protein_median_ae"]:.2f} g')
    print(f'% calories within 50 kcal: {summary["calorie_within_50"]:.1f}%')
    print(f'% calories within 100 kcal: {summary["calorie_within_100"]:.1f}%')
    print(f'% protein within 5 g: {summary["protein_within_5"]:.1f}%')
    print(f'% protein within 10 g: {summary["protein_within_10"]:.1f}%')


async def run() -> None:
    labels_by_dish_id = read_labels_as_dict(BENCHMARK_LABELS_CSV)
    image_paths = get_image_paths(BENCHMARK_IMAGES_DIR)

    print(f"Labels loaded: {len(labels_by_dish_id)}")
    print(f"Images selected for this run: {len(image_paths)}")
    print(f"Results file: {RESULTS_CSV}")

    results = []

    for idx, image_path in enumerate(image_paths, start=1):
        dish_id = image_path.stem
        print(f"[{idx}/{len(image_paths)}] Running {dish_id} ...")

        gt_row = labels_by_dish_id.get(dish_id)
        if gt_row is None:
            results.append(
                {
                    "dish_id": dish_id,
                    "image_path": str(image_path),
                    "calories_gt": None,
                    "protein_gt": None,
                    "calories_pred": None,
                    "protein_pred": None,
                    "calorie_abs_error": None,
                    "protein_abs_error": None,
                    "canonical": None,
                    "nutrition_result": None,
                    "status": "failed",
                    "error_message": "dish_id not found in labels.csv",
                }
            )
            continue

        calories_gt = gt_row["calories_gt"]
        protein_gt = gt_row["protein_gt"]

        if calories_gt is None or protein_gt is None:
            results.append(
                {
                    "dish_id": dish_id,
                    "image_path": str(image_path),
                    "calories_gt": calories_gt,
                    "protein_gt": protein_gt,
                    "calories_pred": None,
                    "protein_pred": None,
                    "calorie_abs_error": None,
                    "protein_abs_error": None,
                    "canonical": None,
                    "nutrition_result": None,
                    "status": "failed",
                    "error_message": "missing calories/protein ground truth in labels.csv",
                }
            )
            continue

        try:
            canonical = await canonicalize_from_image(str(image_path))
            nutrition_result = await estimate_nutrition_from_canonical(canonical)

            preds = extract_predictions(nutrition_result)
            calories_pred = preds["calories_pred"]
            protein_pred = preds["protein_pred"]

            if calories_pred is None or protein_pred is None:
                results.append(
                    {
                        "dish_id": dish_id,
                        "image_path": str(image_path),
                        "calories_gt": calories_gt,
                        "protein_gt": protein_gt,
                        "calories_pred": calories_pred,
                        "protein_pred": protein_pred,
                        "calorie_abs_error": None,
                        "protein_abs_error": None,
                        "canonical": repr(canonical),
                        "nutrition_result": repr(nutrition_result),
                        "status": "failed",
                        "error_message": "missing calories/protein in prediction output",
                    }
                )
                continue

            results.append(
                {
                    "dish_id": dish_id,
                    "image_path": str(image_path),
                    "calories_gt": calories_gt,
                    "protein_gt": protein_gt,
                    "calories_pred": calories_pred,
                    "protein_pred": protein_pred,
                    "calorie_abs_error": abs_error(calories_pred, calories_gt),
                    "protein_abs_error": abs_error(protein_pred, protein_gt),
                    "canonical": repr(canonical),
                    "nutrition_result": repr(nutrition_result),
                    "status": "ok",
                    "error_message": "",
                }
            )

        except Exception as e:
            results.append(
                {
                    "dish_id": dish_id,
                    "image_path": str(image_path),
                    "calories_gt": calories_gt,
                    "protein_gt": protein_gt,
                    "calories_pred": None,
                    "protein_pred": None,
                    "calorie_abs_error": None,
                    "protein_abs_error": None,
                    "canonical": None,
                    "nutrition_result": None,
                    "status": "failed",
                    "error_message": str(e),
                }
            )

    write_results(results, RESULTS_CSV)
    summary = compute_summary(results)
    print_summary(summary)


if __name__ == "__main__":
    asyncio.run(run())