import csv
from pathlib import Path

DATASET_ROOT = Path("/Users/bochkovoy/ACETADA-Dataset")
INPUT_CSV = DATASET_ROOT / "ACETADA-HF-dataset.csv"
OUTPUT_CSV = DATASET_ROOT / "derived" / "ACETADA-HF-dataset.enriched.csv"

NUM_ITEMS = 15


def f(x):
    try:
        return float(x) if x not in (None, "") else None
    except:
        return None


def enrich(row):
    tc = tp = kcal = prot = carb = fat = 0.0
    invalid = 0
    valid = False

    for i in range(1, NUM_ITEMS + 1):
        if not row.get(f"food_item_{i}_name"):
            continue

        b = f(row.get(f"food_item_{i}_before_portion_g"))
        a = f(row.get(f"food_item_{i}_after_portion_g"))
        c = f(row.get(f"food_item_{i}_consumed_g"))

        if (
            b is None or a is None or c is None or
            b < 0 or a < 0 or c < 0 or
            c > b or
            abs((b - a) - c) > 1e-6
        ):
            invalid += 1
            continue

        valid = True
        tc += c
        tp += b
        kcal += f(row.get(f"food_item_{i}_energy_kcal")) or 0
        prot += f(row.get(f"food_item_{i}_protein_g")) or 0
        carb += f(row.get(f"food_item_{i}_carbs_g")) or 0
        fat += f(row.get(f"food_item_{i}_fat_g")) or 0

    ratio = tc / tp if valid and tp > 0 else None

    row.update({
        "cleaned_total_consumed_g": round(tc, 3) if valid else "",
        "cleaned_total_portion_g": round(tp, 3) if valid else "",
        "cleaned_total_kcal": round(kcal, 3) if valid else "",
        "cleaned_total_protein_g": round(prot, 3) if valid else "",
        "cleaned_total_carbs_g": round(carb, 3) if valid else "",
        "cleaned_total_fat_g": round(fat, 3) if valid else "",
        "consumed_ratio": round(ratio, 6) if ratio is not None else "",
        "consumed_ratio_valid": ratio is not None and 0 <= ratio <= 1.000001,
        "invalid_item_count": invalid,
    })

    return row


def main():
    with INPUT_CSV.open() as f:
        reader = csv.DictReader(f)
        rows = [enrich(r) for r in reader]
        fields = reader.fieldnames + [
            "cleaned_total_consumed_g",
            "cleaned_total_portion_g",
            "cleaned_total_kcal",
            "cleaned_total_protein_g",
            "cleaned_total_carbs_g",
            "cleaned_total_fat_g",
            "consumed_ratio",
            "consumed_ratio_valid",
            "invalid_item_count",
        ]

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()