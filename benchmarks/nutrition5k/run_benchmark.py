import asyncio
import csv
from pathlib import Path

from vision import estimate_meal


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_ROOT = Path("/Volumes/T7/Library/nutrition5k_benchmark_dataset_builder")
LABELS_CSV = DATASET_ROOT / "data/labels/labels.csv"
RESULTS_CSV = PROJECT_ROOT / "benchmarks/nutrition5k/results.csv"

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
        "calorie_abs_error": None,
        "protein_abs_error": None,
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
            res["error_message"] = "invalid prediction"
            return res

        res.update(
            {
                "dish_pred": pred.get("dish"),
                "calories_pred": calories,
                "protein_pred": protein,
                "calorie_abs_error": abs(calories - row["calories_gt"]),
                "protein_abs_error": abs(protein - row["protein_gt"]),
                "status": "ok",
            }
        )

        return res

    except Exception as e:
        res["error_message"] = str(e)
        return res


def write_results(results, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    fields = list(results[0].keys())

    valid = [r for r in results if r["status"] == "ok"]

    def avg(xs):
        return sum(xs) / len(xs) if xs else None

    summary = {
        "dish_id": "SUMMARY",
        "calorie_abs_error": avg(
            [r["calorie_abs_error"] for r in valid if r["calorie_abs_error"]]
        ),
        "protein_abs_error": avg(
            [r["protein_abs_error"] for r in valid if r["protein_abs_error"]]
        ),
        "status": f"rows_ok={len(valid)}",
    }

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)
        w.writerow(summary)


async def run():
    rows = read_rows(LABELS_CSV)

    print(f"Processing {len(rows)} rows")

    results = []
    for i, row in enumerate(rows, 1):
        print(f"[{i}/{len(rows)}] {row['dish_id']}_{row['camera']}")
        results.append(await process_row(row))

    write_results(results, RESULTS_CSV)
    print("Done")


if __name__ == "__main__":
    asyncio.run(run())