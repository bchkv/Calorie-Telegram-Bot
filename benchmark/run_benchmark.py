import asyncio
import csv
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

MAX_IMAGES = 20  # None = process all images

DISH_ID_COLUMN = "dish_id"
CALORIES_GT_COLUMN = "calories"
PROTEIN_GT_COLUMN = "protein"


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

    if MAX_IMAGES is not None:
        image_paths = image_paths[:MAX_IMAGES]

    return image_paths


def abs_error(pred: float, gt: float) -> float:
    return abs(pred - gt)


def extract_predictions(nutrition_result: dict) -> dict[str, float | None]:
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
        "status",
        "error_message",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


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
                    "status": "failed",
                    "error_message": str(e),
                }
            )

    write_results(results, RESULTS_CSV)
    print("Done.")