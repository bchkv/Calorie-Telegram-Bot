from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = ROOT / "datasets" / "nutritionverse"
IMAGES_PATH = DATASET_PATH / "images"
METADATA_PATH = DATASET_PATH / "metadata.csv"
