Source: https://skynet.ecn.purdue.edu/~coburn6/ACETADA/

# TODO

## Confirm the dataset accounts only for eaten calories


## Filter meals that were fully eaten

Cause the dataset accounts only for eaten calories 




# ACETADA CSV Schema (Short Overview)

`ACETADA-HF-dataset.csv` contains **one row per meal**. Each row links two images and detailed nutrition labels.

## Images
Two photos are recorded for every meal:

- **before_*** — image taken before eating (full meal).
- **after_*** — image taken after eating (leftovers).

Fields include filename, filepath, timestamp, and GPS coordinates.

## Food Items
Meals can contain up to **15 food items**. Each item uses repeating columns:

- `food_item_X_name`
- `food_item_X_before_portion_g`
- `food_item_X_after_portion_g`
- `food_item_X_consumed_g`
- `food_item_X_energy_kcal`
- `food_item_X_carbs_g`
- `food_item_X_protein_g`
- `food_item_X_fat_g`

`consumed_g = before_portion_g − after_portion_g`.

## Meal Metadata
Additional fields describe the meal:

- `food_item_count`
- `meal_type` (Breakfast / Lunch / Dinner)
- `participant_id`

## Aggregated Nutrition
Meal-level totals are provided:

- `total_portion_g` — food served
- `total_consumed_g` — food eaten
- `total_kcal`
- `total_carbs_g`
- `total_protein_g`
- `total_fat_g`
