import asyncio
import csv
import json
from pathlib import Path

from vision import estimate_meal


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_ROOT = Path("/Volumes/T7/Library/nutrition5k_benchmark_dataset_builder")
LABELS_CSV = DATASET_ROOT / "data/labels/labels.csv"

BENCHMARK_DIR = PROJECT_ROOT / "nutrition5k"
RESULTS_CSV = BENCHMARK_DIR / "results.csv"
SUMMARY_JSON = BENCHMARK_DIR / "summary.json"

MAX_IMAGES = 20


def safe_float(x):
    try:
        return float(x)
    except:
        return None


def read_rows(path: Path):
    with path.open() as f:
        rows = list(csv.DictReader(f))

    rows = [
        {
            "dish_id": r["dish_id"].strip(),
            "camera": r["camera"].strip(),
            "image_path": r["image_path"].strip(),
            "calories_gt": safe_float(r["calories"]),
            "protein_gt": safe_float(r["protein_g"]),
        }
        for r in rows
    ]

    return rows[:MAX_IMAGES] if MAX_IMAGES else rows


def base_result(row, image_path):
    return {
        "dish_id": row["dish_id"],
        "camera": row["camera"],
        "image_path": str(image_path),
        "calories_gt": row["calories_gt"],
        "protein_gt": row["protein_gt"],
        "dish_pred": None,
        "calories_pred": None,
        "protein_pred": None,
        "calorie_error": None,
        "protein_error": None,
        "calorie_abs_error": None,
        "protein_abs_error": None,
        "calorie_pct_error": None,
        "protein_pct_error": None,
        "status": "failed",
        "error_message": "",
    }


async def process_row(row):
    image_path = DATASET_ROOT / row["image_path"]
    res = base_result(row, image_path)

    if not image_path.exists():
        res["error_message"] = "image not found"
        return res

    if row["calories_gt"] is None or row["protein_gt"] is None:
        res["error_message"] = "missing ground truth"
        return res

    try:
        pred = await estimate_meal(str(image_path))

        calories = safe_float(pred.get("calories"))
        protein = safe_float(pred.get("protein"))

        if calories is None or protein is None:
            res["dish_pred"] = pred.get("dish")
            res["error_message"] = "invalid prediction"
            return res

        calorie_error = calories - row["calories_gt"]
        protein_error = protein - row["protein_gt"]

        calorie_pct_error = None
        if row["calories_gt"] not in (None, 0):
            calorie_pct_error = abs(calorie_error) / row["calories_gt"]

        protein_pct_error = None
        if row["protein_gt"] not in (None, 0):
            protein_pct_error = abs(protein_error) / row["protein_gt"]

        res.update(
            {
                "dish_pred": pred.get("dish"),
                "calories_pred": calories,
                "protein_pred": protein,
                "calorie_error": calorie_error,
                "protein_error": protein_error,
                "calorie_abs_error": abs(calorie_error),
                "protein_abs_error": abs(protein_error),
                "calorie_pct_error": calorie_pct_error,
                "protein_pct_error": protein_pct_error,
                "status": "ok",
            }
        )

        return res

    except Exception as e:
        res["error_message"] = str(e)
        return res


def avg(xs):
    return sum(xs) / len(xs) if xs else None


def write_results(results, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    fields = list(results[0].keys())

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)


def build_summary(results):
    valid = [r for r in results if r["status"] == "ok"]

    calorie_abs_errors = [r["calorie_abs_error"] for r in valid if r["calorie_abs_error"] is not None]
    protein_abs_errors = [r["protein_abs_error"] for r in valid if r["protein_abs_error"] is not None]

    calorie_errors = [r["calorie_error"] for r in valid if r["calorie_error"] is not None]
    protein_errors = [r["protein_error"] for r in valid if r["protein_error"] is not None]

    total_true_calories = sum(r["calories_gt"] for r in valid if r["calories_gt"] is not None)
    total_pred_calories = sum(r["calories_pred"] for r in valid if r["calories_pred"] is not None)

    total_calorie_error = total_pred_calories - total_true_calories
    relative_total_calorie_error = (
        total_calorie_error / total_true_calories
        if total_true_calories not in (None, 0)
        else None
    )

    return {
        "dataset_csv": str(LABELS_CSV),
        "dataset_root": str(DATASET_ROOT),
        "results_csv": str(RESULTS_CSV),
        "max_rows": MAX_IMAGES,
        "rows_total": len(results),
        "rows_ok": len(valid),
        "rows_failed": len(results) - len(valid),
        "rows_with_calorie_prediction": len([r for r in valid if r["calories_pred"] is not None]),
        "rows_with_protein_prediction": len([r for r in valid if r["protein_pred"] is not None]),
        "final_mae_calories": avg(calorie_abs_errors),
        "final_mae_protein": avg(protein_abs_errors),
        "final_cumulative_calorie_error": sum(calorie_errors) if calorie_errors else None,
        "final_cumulative_protein_error": sum(protein_errors) if protein_errors else None,
        "final_mean_signed_calorie_error": avg(calorie_errors),
        "final_mean_signed_protein_error": avg(protein_errors),
        "final_total_true_calories": total_true_calories,
        "final_total_pred_calories": total_pred_calories,
        "final_total_calorie_error": total_calorie_error,
        "final_relative_total_calorie_error": relative_total_calorie_error,
    }


def write_summary(summary, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


async def run():
    rows = read_rows(LABELS_CSV)

    print(f"Processing {len(rows)} rows")
    print(f"Results: {RESULTS_CSV}")
    print(f"Summary: {SUMMARY_JSON}")

    results = []
    for i, row in enumerate(rows, 1):
        print(f"[{i}/{len(rows)}] {row['dish_id']}_{row['camera']}")
        results.append(await process_row(row))

    write_results(results, RESULTS_CSV)

    summary = build_summary(results)
    write_summary(summary, SUMMARY_JSON)

    print("Done")


if __name__ == "__main__":
    asyncio.run(run())