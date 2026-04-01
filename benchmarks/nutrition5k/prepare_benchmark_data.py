from __future__ import annotations

import csv
from pathlib import Path

# Absolute path to the directory where this script lives.
# Example:
# benchmarks/nutrition5k/
SCRIPT_DIR = Path(__file__).resolve().parent

# Project root, assuming the script is in benchmarks/nutrition5k/
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Input raw metadata CSV.
# Change this if you want cafe2 instead of cafe1.
INPUT_CSV = PROJECT_ROOT / "data/raw/nutrition5k/nutrition5k_benchmark_dataset_builder/metadata/dish_metadata_cafe1.csv"

# Output cleaned benchmark CSV.
OUTPUT_CSV = PROJECT_ROOT / "benchmarks/nutrition5k/nutrition5k_benchmark_clean.csv"


def to_float(value: str) -> float | None:
    """
    Convert a CSV string value to float.

    Returns:
        - float if conversion succeeds
        - None if the value is empty / missing / invalid
    """
    if value is None:
        return None

    value = value.strip()
    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def parse_raw_row(row: list[str]) -> dict[str, object] | None:
    """
    Parse one raw Nutrition5k metadata row.

    Raw layout:
        dish_id,
        total_calories,
        total_mass,
        total_fat,
        total_carb,
        total_protein,
        ingr_1_id, ingr_1_name, ingr_1_grams, ingr_1_calories, ingr_1_fat, ingr_1_carb, ingr_1_protein,
        ingr_2_id, ingr_2_name, ...
    """
    if len(row) < 6:
        return None

    dish_id = row[0].strip()
    groundtruth_calories = to_float(row[1])
    total_portion_g = to_float(row[2])
    groundtruth_protein_g = to_float(row[5])

    if (
        not dish_id
        or total_portion_g is None
        or groundtruth_calories is None
        or groundtruth_protein_g is None
    ):
        return None

    if total_portion_g <= 0 or groundtruth_calories < 0 or groundtruth_protein_g < 0:
        return None

    ingredient_names: list[str] = []
    ingredient_chunk_size = 7

    for i in range(6, len(row), ingredient_chunk_size):
        chunk = row[i:i + ingredient_chunk_size]

        if len(chunk) < ingredient_chunk_size:
            continue

        ingr_id = chunk[0].strip()
        ingr_name = chunk[1].strip()

        if not ingr_id and not ingr_name:
            continue

        if ingr_name:
            ingredient_names.append(ingr_name)

    groundtruth_content = ", ".join(ingredient_names)

    return {
        "sample_id": dish_id,
        "total_portion_g": total_portion_g,
        "groundtruth_calories": groundtruth_calories,
        "groundtruth_protein_g": groundtruth_protein_g,
        "groundtruth_content": groundtruth_content,
    }


def main() -> None:
    """
    Read the raw dish metadata CSV and write a compact benchmark-ready CSV.

    Output schema:
        sample_id
        total_portion_g
        groundtruth_calories
        groundtruth_protein_g
        groundtruth_content
    """
    input_path = Path(INPUT_CSV)
    output_path = Path(OUTPUT_CSV)

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    fieldnames = [
        "sample_id",
        "total_portion_g",
        "groundtruth_calories",
        "groundtruth_protein_g",
        "groundtruth_content",
    ]

    kept = 0
    skipped = 0

    with input_path.open("r", encoding="utf-8-sig", newline="") as f_in, \
         output_path.open("w", encoding="utf-8", newline="") as f_out:

        reader = csv.reader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for raw_row in reader:
            parsed = parse_raw_row(raw_row)

            if parsed is None:
                skipped += 1
                continue

            cleaned_row = {
                "sample_id": parsed["sample_id"],
                "total_portion_g": f"{parsed['total_portion_g']:.6f}".rstrip("0").rstrip("."),
                "groundtruth_calories": f"{parsed['groundtruth_calories']:.6f}".rstrip("0").rstrip("."),
                "groundtruth_protein_g": f"{parsed['groundtruth_protein_g']:.6f}".rstrip("0").rstrip("."),
                "groundtruth_content": parsed["groundtruth_content"],
            }

            writer.writerow(cleaned_row)
            kept += 1

    print(f"Done. Kept {kept} rows, skipped {skipped} rows.")
    print(f"Saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()