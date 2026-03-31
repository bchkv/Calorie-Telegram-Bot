See https://github.com/google-research-datasets/Nutrition5k for details.

## Dish Metadata

The dish metadata CSVs (metadata/dish_metadata_cafe1.csv and metadata/dish_metadata_cafe2.csv) contain all nutrition metadata at the dish-level, as well as per-ingredient mass and macronutrients. For each dish ID dish_[10 digit timestamp], there is a CSV entry containing the following fields:

dish_id, total_calories, total_mass, total_fat, total_carb, total_protein, num_ingrs, (ingr_1_id, ingr_1_name, ingr_1_grams, ingr_1_calories, ingr_1_fat, ingr_1_carb, ingr_1_protein, ...)

with the last 8 fields are repeated for every ingredient present in the dish.

## Clean nutrition5k schema

sample_id — copied from dish_id
dish_id — copied from dish_id
total_portion_g — renamed from total_mass
groundtruth_calories — renamed from total_calories
groundtruth_protein_g — renamed from total_protein
groundtruth_content — built by comma-joining all ingr_X_name values
