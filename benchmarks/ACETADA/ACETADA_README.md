Source: https://skynet.ecn.purdue.edu/~coburn6/ACETADA/

# The orginal ACETADA CSV Schema

before_…: Metadata for the image taken before the meal (date, time, GPS, file path). Images are relative to the dataset root (e.g., ACETADA/3001/2021-03-11_07-26-01.jpg).
after_…: Metadata for the image taken after the meal (date, time, GPS, file path).
food_item_X_… (1–15):

    _name: food item name
    _before_portion_g: grams served
    _after_portion_g: grams remaining
    _consumed_g: before - after
    _energy_kcal, _carbs_g, _protein_g, _fat_g

food_item_count: number of items in the meal
meal_type: breakfast/lunch/dinner
participant_id: second-level directory in file paths
total_…: meal-level aggregates (total_kcal, total_carbs_g, etc.)

# Clean ACETADA schema

sample_id — stable row id (acetada_000XXX)
before_filename — image filename used for inference
total_portion_g — total served meal weight (grams)
eaten_ratio — total_consumed_g / total_portion_g
groundtruth_calories — total_kcal (consumed calories)
groundtruth_protein_g — total_protein_g (consumed protein)
groundtruth_content — comma-joined food_item_X_name values

## Faulty rows were filtered:
missing values / empty filename → drop
total_portion_g ≤ 0 → drop
any negative meal totals → drop
any negative item portion fields → drop
eaten_ratio ≤ 0.95 → drop
eaten_ratio > 1.02 → drop

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
