import asyncio
import csv
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from vision import estimate_meal


BENCHMARK_DATASET_ROOT = Path(
    "/Volumes/T7/Library/nutrition5k_benchmark_dataset_builder"
)
BENCHMARK_LABELS_CSV = BENCHMARK_DATASET_ROOT / "data/labels/labels.csv"
RESULTS_CSV = PROJECT_ROOT / "benchmark/results/benchmark_results.csv"

MAX_IMAGES = 20  # None = process all rows


def safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_rows(csv_path: Path) -> list[dict]:
    rows = []

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            rows.append(
                {
                    "dish_id": str(row["dish_id"]).strip(),
                    "camera": str(row["camera"]).strip(),
                    "image_path": str(row["image_path"]).strip(),
                    "calories_gt": safe_float(row["calories"]),
                    "protein_gt": safe_float(row["protein_g"]),
                }
            )

    if MAX_IMAGES is not None:
        rows = rows[:MAX_IMAGES]

    return rows


def abs_error(pred: float, gt: float) -> float:
    return abs(pred - gt)


def pct_error(pred: float, gt: float) -> float | None:
    if gt == 0:
        return None
    return abs(pred - gt) / gt * 100


def write_results(results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "dish_id",
        "camera",
        "image_path",
        "calories_gt",
        "protein_gt",
        "dish_pred",
        "calories_pred",
        "protein_pred",
        "calorie_abs_error",
        "protein_abs_error",
        "status",
        "error_message",
    ]

    valid_rows = [row for row in results if row["status"] == "ok"]

    calorie_abs_errors = [
        row["calorie_abs_error"]
        for row in valid_rows
        if row["calorie_abs_error"] is not None
    ]
    protein_abs_errors = [
        row["protein_abs_error"]
        for row in valid_rows
        if row["protein_abs_error"] is not None
    ]

    calorie_pct_errors = []
    protein_pct_errors = []

    for row in valid_rows:
        if row["calories_pred"] is not None and row["calories_gt"] is not None:
            err = pct_error(row["calories_pred"], row["calories_gt"])
            if err is not None:
                calorie_pct_errors.append(err)

        if row["protein_pred"] is not None and row["protein_gt"] is not None:
            err = pct_error(row["protein_pred"], row["protein_gt"])
            if err is not None:
                protein_pct_errors.append(err)

    summary_row = {
        "dish_id": "SUMMARY",
        "camera": "",
        "image_path": "",
        "calories_gt": "",
        "protein_gt": "",
        "dish_pred": "",
        "calories_pred": "",
        "protein_pred": "",
        "calorie_abs_error": (
            sum(calorie_abs_errors) / len(calorie_abs_errors)
            if calorie_abs_errors
            else ""
        ),
        "protein_abs_error": (
            sum(protein_abs_errors) / len(protein_abs_errors)
            if protein_abs_errors
            else ""
        ),
        "status": (
            f"calorie_pct_error={sum(calorie_pct_errors) / len(calorie_pct_errors):.2f}%; "
            f"protein_pct_error={sum(protein_pct_errors) / len(protein_pct_errors):.2f}%"
            if calorie_pct_errors and protein_pct_errors
            else ""
        ),
        "error_message": "",
    }

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        writer.writerow(summary_row)


async def run() -> None:
    rows = read_rows(BENCHMARK_LABELS_CSV)

    print(f"Rows selected for this run: {len(rows)}")
    print(f"Results file: {RESULTS_CSV}")

    results = []

    for idx, row in enumerate(rows, start=1):
        dish_id = row["dish_id"]
        camera = row["camera"]
        image_path = BENCHMARK_DATASET_ROOT / row["image_path"]
        calories_gt = row["calories_gt"]
        protein_gt = row["protein_gt"]

        print(f"[{idx}/{len(rows)}] Running {dish_id}_{camera} ...")
        print(f"Image: {image_path}")

        if not image_path.exists():
            results.append(
                {
                    "dish_id": dish_id,
                    "camera": camera,
                    "image_path": str(image_path),
                    "calories_gt": calories_gt,
                    "protein_gt": protein_gt,
                    "dish_pred": None,
                    "calories_pred": None,
                    "protein_pred": None,
                    "calorie_abs_error": None,
                    "protein_abs_error": None,
                    "status": "failed",
                    "error_message": "image file not found",
                }
            )
            continue

        if calories_gt is None or protein_gt is None:
            results.append(
                {
                    "dish_id": dish_id,
                    "camera": camera,
                    "image_path": str(image_path),
                    "calories_gt": calories_gt,
                    "protein_gt": protein_gt,
                    "dish_pred": None,
                    "calories_pred": None,
                    "protein_pred": None,
                    "calorie_abs_error": None,
                    "protein_abs_error": None,
                    "status": "failed",
                    "error_message": "missing calories/protein ground truth in labels.csv",
                }
            )
            continue

        try:
            result = await estimate_meal(str(image_path))

            dish_pred = result.get("dish")
            calories_pred = safe_float(result.get("calories"))
            protein_pred = safe_float(result.get("protein"))

            if calories_pred is None or protein_pred is None:
                results.append(
                    {
                        "dish_id": dish_id,
                        "camera": camera,
                        "image_path": str(image_path),
                        "calories_gt": calories_gt,
                        "protein_gt": protein_gt,
                        "dish_pred": dish_pred,
                        "calories_pred": calories_pred,
                        "protein_pred": protein_pred,
                        "calorie_abs_error": None,
                        "protein_abs_error": None,
                        "status": "failed",
                        "error_message": "missing calories/protein in prediction output",
                    }
                )
                continue

            results.append(
                {
                    "dish_id": dish_id,
                    "camera": camera,
                    "image_path": str(image_path),
                    "calories_gt": calories_gt,
                    "protein_gt": protein_gt,
                    "dish_pred": dish_pred,
                    "calories_pred": calories_pred,
                    "protein_pred": protein_pred,
                    "calorie_abs_error": abs_error(calories_pred, calories_gt),
                    "protein_abs_error": abs_error(protein_pred, protein_gt),
                    "status": "ok",
                    "error_message": "",
                }
            )

        except Exception as e:
            results.append(
                {
                    "dish_id": dish_id,
                    "camera": camera,
                    "image_path": str(image_path),
                    "calories_gt": calories_gt,
                    "protein_gt": protein_gt,
                    "dish_pred": None,
                    "calories_pred": None,
                    "protein_pred": None,
                    "calorie_abs_error": None,
                    "protein_abs_error": None,
                    "status": "failed",
                    "error_message": str(e),
                }
            )

    write_results(results, RESULTS_CSV)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(run())