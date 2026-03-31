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

# Results schema

## results.csv
sample_id — unique row identifier
groundtruth_calories — reference calories
predicted_calories — model calories prediction
calorie_error_signed — predicted minus groundtruth
calorie_error_abs — absolute calorie error
groundtruth_protein_g — reference protein
predicted_protein_g — model protein prediction
protein_error_signed_g — predicted minus groundtruth
protein_error_abs_g — absolute protein error
groundtruth_content — reference ingredient list
predicted_content — model-predicted ingredient list
status — ok / failed

## summary.json
rows_total — total rows in benchmark input
rows_ok — successfully predicted rows
rows_failed — failed rows
total_groundtruth_calories — sum of reference calories
total_predicted_calories — sum of predicted calories
total_groundtruth_protein_g — sum of reference protein
total_predicted_protein_g — sum of predicted protein
cumulative_error_calories_signed — total predicted minus total groundtruth calories
cumulative_error_protein_signed_g — total predicted minus total groundtruth protein
mean_error_calories_abs — average absolute calorie error
mean_error_protein_abs_g — average absolute protein error
