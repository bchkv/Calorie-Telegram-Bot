from __future__ import annotations

import csv
from pathlib import Path

# Absolute path to the directory where this script lives:
# benchmarks/ACETADA/
SCRIPT_DIR = Path(__file__).resolve().parent

# Project root, assuming the script is in benchmarks/ACETADA/
# so parent.parent goes back to the repository root.
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Input raw ACETADA CSV.
INPUT_CSV = PROJECT_ROOT / "data" / "raw" / "ACETADA" / "ACETADA-HF-dataset.csv"

# Output cleaned benchmark CSV.
OUTPUT_CSV = SCRIPT_DIR / "acetada_benchmark_clean.csv"

# Keep only meals whose consumed/served ratio is within this range.
# Lower bound filters out partially eaten meals.
# Upper bound filters out clearly inconsistent / broken rows.
EATEN_RATIO_MIN = 0.95
EATEN_RATIO_MAX = 1.02

# ACETADA has up to 15 food items per meal.
MAX_ITEMS = 15


def to_float(value: str) -> float | None:
    """
    Convert a CSV string value to float.

    Returns:
        - float value if conversion succeeds
        - None if the value is empty / missing / not parseable
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


def build_groundtruth_content(row: dict[str, str]) -> str:
    """
    Build one combined text field describing the meal contents.

    Example output:
        "Black tea (no milk), Toast multigrain or white, Jam"

    Logic:
        - iterate over food_item_1_name ... food_item_15_name
        - keep only non-empty names
        - preserve original item order
        - join into one comma-separated string
    """
    items: list[str] = []

    for i in range(1, MAX_ITEMS + 1):
        name = (row.get(f"food_item_{i}_name") or "").strip()
        if name:
            items.append(name)

    return ", ".join(items)


def has_negative_portion_fields(row: dict[str, str]) -> bool:
    """
    Check whether any item-level portion field is negative.

    We exclude rows if any of these are negative:
        - food_item_X_before_portion_g
        - food_item_X_after_portion_g
        - food_item_X_consumed_g

    Why:
        negative gram amounts are physically invalid for this benchmark
        and usually indicate annotation / data corruption issues.
    """
    for i in range(1, MAX_ITEMS + 1):
        for field in (
            f"food_item_{i}_before_portion_g",
            f"food_item_{i}_after_portion_g",
            f"food_item_{i}_consumed_g",
        ):
            value = to_float(row.get(field, ""))
            if value is not None and value < 0:
                return True

    return False


def has_negative_meal_totals(
    total_portion_g: float,
    total_consumed_g: float,
    groundtruth_calories: float,
    groundtruth_protein_g: float,
) -> bool:
    """
    Check whether any important meal-level totals are negative.

    We exclude rows if any of these are negative:
        - total_portion_g
        - total_consumed_g
        - total_kcal
        - total_protein_g
    """
    return any(
        value < 0
        for value in (
            total_portion_g,
            total_consumed_g,
            groundtruth_calories,
            groundtruth_protein_g,
        )
    )


def main() -> None:
    """
    Read the raw ACETADA CSV, filter invalid / misaligned rows,
    and write a compact benchmark-ready CSV.

    Output schema:
        sample_id
        before_filename
        total_portion_g
        eaten_ratio
        groundtruth_calories
        groundtruth_protein_g
        groundtruth_content
    """
    input_path = Path(INPUT_CSV)
    output_path = Path(OUTPUT_CSV)

    # Fail early with a clear error if the source file is missing.
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    with input_path.open("r", encoding="utf-8-sig", newline="") as f_in, \
         output_path.open("w", encoding="utf-8", newline="") as f_out:

        # Read raw CSV rows as dicts: column_name -> cell_value
        reader = csv.DictReader(f_in)

        # Final compact benchmark schema.
        fieldnames = [
            "sample_id",
            "before_filename",
            "total_portion_g",
            "eaten_ratio",
            "groundtruth_calories",
            "groundtruth_protein_g",
            "groundtruth_content",
        ]

        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        kept = 0
        skipped = 0

        # row_idx refers to the original raw CSV row number within the data section
        # (excluding the header), starting from 1.
        for row_idx, row in enumerate(reader, start=1):
            # Parse the raw fields we care about.
            total_portion_g = to_float(row.get("total_portion_g", ""))
            total_consumed_g = to_float(row.get("total_consumed_g", ""))
            groundtruth_calories = to_float(row.get("total_kcal", ""))
            groundtruth_protein_g = to_float(row.get("total_protein_g", ""))
            before_filename = (row.get("before_filename") or "").strip()

            # Basic validation:
            # skip rows with missing essential fields,
            # missing image filename, or non-positive served weight.
            if (
                total_portion_g is None
                or total_consumed_g is None
                or groundtruth_calories is None
                or groundtruth_protein_g is None
                or not before_filename
                or total_portion_g <= 0
            ):
                skipped += 1
                continue

            # Exclude rows with invalid negative meal-level totals.
            if has_negative_meal_totals(
                total_portion_g=total_portion_g,
                total_consumed_g=total_consumed_g,
                groundtruth_calories=groundtruth_calories,
                groundtruth_protein_g=groundtruth_protein_g,
            ):
                skipped += 1
                continue

            # Exclude rows with invalid negative item-level portion values.
            if has_negative_portion_fields(row):
                skipped += 1
                continue

            # Compute the eaten ratio:
            # how much of the served meal was consumed.
            eaten_ratio = total_consumed_g / total_portion_g

            # Keep only near-fully-eaten meals and reject clearly broken ratios.
            if not (EATEN_RATIO_MIN < eaten_ratio <= EATEN_RATIO_MAX):
                skipped += 1
                continue

            # Build one text field describing the meal composition.
            groundtruth_content = build_groundtruth_content(row)

            # Create the cleaned output row.
            cleaned_row = {
                # Stable ID based on original raw row position.
                "sample_id": f"acetada_{row_idx:06d}",

                # Image file to benchmark on.
                "before_filename": before_filename,

                # Served meal mass in grams.
                "total_portion_g": f"{total_portion_g:.6f}".rstrip("0").rstrip("."),

                # Consumed / served.
                "eaten_ratio": f"{eaten_ratio:.6f}".rstrip("0").rstrip("."),

                # Ground-truth meal labels.
                "groundtruth_calories": f"{groundtruth_calories:.6f}".rstrip("0").rstrip("."),
                "groundtruth_protein_g": f"{groundtruth_protein_g:.6f}".rstrip("0").rstrip("."),

                # Human-readable description of what the meal contains.
                "groundtruth_content": groundtruth_content,
            }

            writer.writerow(cleaned_row)
            kept += 1

    print(f"Done. Kept {kept} rows, skipped {skipped} rows.")
    print(f"Saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()