from __future__ import annotations

import asyncio
import csv
import json
import random
from pathlib import Path
from typing import Any

from src.vision import estimate_meal


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

BENCHMARK_CSV = SCRIPT_DIR / "nutrition5k_benchmark_clean.csv"
RESULTS_CSV = SCRIPT_DIR / "results.csv"
SUMMARY_JSON = SCRIPT_DIR / "summary.json"

# Directory with selected benchmark images.
# Adjust if your images live somewhere else.
IMAGE_DIR = PROJECT_ROOT / "data" / "processed" / "frames_selected"

# Which frame variant to use for each dish.
# Common choices in Nutrition5k-derived pipelines are "_B.png" or "_C.png".
IMAGE_SUFFIX = "_B.png"

# Max number of dishes to process.
# Set to None to process all rows.
MAX_ROWS: int | None = 3

# True -> random sample of MAX_ROWS rows
# False -> first MAX_ROWS rows
RANDOM_SAMPLE = False
RANDOM_SEED = 333


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()
    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def format_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}".rstrip("0").rstrip(".")


def load_benchmark_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def select_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if MAX_ROWS is None or MAX_ROWS >= len(rows):
        return rows

    if RANDOM_SAMPLE:
        rng = random.Random(RANDOM_SEED)
        return rng.sample(rows, MAX_ROWS)

    return rows[:MAX_ROWS]


def safe_extract_prediction(prediction: Any) -> tuple[str, float | None, float | None]:
    if prediction is None:
        return "", None, None

    if isinstance(prediction, dict):
        predicted_content = str(prediction.get("dish", "") or "").strip()
        predicted_calories = to_float(prediction.get("calories"))
        predicted_protein_g = to_float(prediction.get("protein"))
        return predicted_content, predicted_calories, predicted_protein_g

    return str(prediction).strip(), None, None


def get_image_path(sample_id: str) -> Path:
    """
    Build the image path for a cleaned Nutrition5k benchmark row.

    Example:
        sample_id = "dish_1561662216"
        IMAGE_SUFFIX = "_B.png"
        -> .../frames_selected/dish_1561662216_B.png
    """
    return IMAGE_DIR / f"{sample_id}{IMAGE_SUFFIX}"


def write_results_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "sample_id",
        "groundtruth_calories",
        "predicted_calories",
        "calorie_error_signed",
        "calorie_error_abs",
        "groundtruth_protein_g",
        "predicted_protein_g",
        "protein_error_signed_g",
        "protein_error_abs_g",
        "groundtruth_content",
        "predicted_content",
        "status",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_json(summary: dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


async def process_row(row: dict[str, str]) -> dict[str, Any]:
    sample_id = (row.get("sample_id") or "").strip()
    groundtruth_content = (row.get("groundtruth_content") or "").strip()

    groundtruth_calories = to_float(row.get("groundtruth_calories"))
    groundtruth_protein_g = to_float(row.get("groundtruth_protein_g"))

    result = {
        "sample_id": sample_id,
        "groundtruth_calories": format_number(groundtruth_calories),
        "predicted_calories": "",
        "calorie_error_signed": "",
        "calorie_error_abs": "",
        "groundtruth_protein_g": format_number(groundtruth_protein_g),
        "predicted_protein_g": "",
        "protein_error_signed_g": "",
        "protein_error_abs_g": "",
        "groundtruth_content": groundtruth_content,
        "predicted_content": "",
        "status": "failed",
    }

    if not sample_id:
        return result

    if groundtruth_calories is None or groundtruth_protein_g is None:
        return result

    image_path = get_image_path(sample_id)
    if not image_path.exists():
        return result

    try:
        prediction = await estimate_meal(
            image_path=str(image_path),
            description=None,
        )

        predicted_content, predicted_calories, predicted_protein_g = safe_extract_prediction(prediction)

        if predicted_calories is None or predicted_protein_g is None:
            return result

        calorie_error_signed = predicted_calories - groundtruth_calories
        calorie_error_abs = abs(calorie_error_signed)

        protein_error_signed_g = predicted_protein_g - groundtruth_protein_g
        protein_error_abs_g = abs(protein_error_signed_g)

        result.update(
            {
                "predicted_calories": format_number(predicted_calories),
                "calorie_error_signed": format_number(calorie_error_signed),
                "calorie_error_abs": format_number(calorie_error_abs),
                "predicted_protein_g": format_number(predicted_protein_g),
                "protein_error_signed_g": format_number(protein_error_signed_g),
                "protein_error_abs_g": format_number(protein_error_abs_g),
                "predicted_content": predicted_content,
                "status": "ok",
            }
        )
        return result

    except Exception:
        return result


async def main() -> None:
    if not BENCHMARK_CSV.exists():
        raise FileNotFoundError(f"Benchmark CSV not found: {BENCHMARK_CSV}")

    if not IMAGE_DIR.exists():
        raise FileNotFoundError(f"Image directory not found: {IMAGE_DIR}")

    all_rows = load_benchmark_rows(BENCHMARK_CSV)
    selected_rows = select_rows(all_rows)

    results: list[dict[str, Any]] = []

    for idx, row in enumerate(selected_rows, start=1):
        print(f"[{idx}/{len(selected_rows)}] Processing {row.get('sample_id', '')}...")
        result = await process_row(row)
        results.append(result)

    rows_total = len(results)
    rows_ok = sum(1 for r in results if r["status"] == "ok")
    rows_failed = rows_total - rows_ok

    ok_rows = [r for r in results if r["status"] == "ok"]

    total_groundtruth_calories = sum(to_float(r["groundtruth_calories"]) or 0.0 for r in ok_rows)
    total_predicted_calories = sum(to_float(r["predicted_calories"]) or 0.0 for r in ok_rows)
    total_groundtruth_protein_g = sum(to_float(r["groundtruth_protein_g"]) or 0.0 for r in ok_rows)
    total_predicted_protein_g = sum(to_float(r["predicted_protein_g"]) or 0.0 for r in ok_rows)

    mean_error_calories_abs = (
        sum(to_float(r["calorie_error_abs"]) or 0.0 for r in ok_rows) / rows_ok
        if rows_ok
        else None
    )
    mean_error_protein_abs_g = (
        sum(to_float(r["protein_error_abs_g"]) or 0.0 for r in ok_rows) / rows_ok
        if rows_ok
        else None
    )

    summary = {
        "rows_total": rows_total,
        "rows_ok": rows_ok,
        "rows_failed": rows_failed,
        "total_groundtruth_calories": format_number(total_groundtruth_calories),
        "total_predicted_calories": format_number(total_predicted_calories),
        "total_groundtruth_protein_g": format_number(total_groundtruth_protein_g),
        "total_predicted_protein_g": format_number(total_predicted_protein_g),
        "cumulative_error_calories_signed": format_number(total_predicted_calories - total_groundtruth_calories),
        "cumulative_error_protein_signed_g": format_number(total_predicted_protein_g - total_groundtruth_protein_g),
        "mean_error_calories_abs": format_number(mean_error_calories_abs),
        "mean_error_protein_abs_g": format_number(mean_error_protein_abs_g),
    }

    write_results_csv(results, RESULTS_CSV)
    write_summary_json(summary, SUMMARY_JSON)

    print(f"Done. Processed {rows_total} rows.")
    print(f"rows_ok={rows_ok}, rows_failed={rows_failed}")
    print(f"Saved results to: {RESULTS_CSV}")
    print(f"Saved summary to: {SUMMARY_JSON}")


if __name__ == "__main__":
    asyncio.run(main())