# The results schema

results.csv (per meal)
sample_id — unique row identifier
before_filename — image file used for prediction
groundtruth_calories — reference calories (kcal)
predicted_calories — model calories prediction
calorie_error_signed — predicted minus groundtruth
calorie_error_abs — absolute calorie error
groundtruth_protein_g — reference protein (g)
predicted_protein_g — model protein prediction
protein_error_signed_g — predicted minus groundtruth
protein_error_abs_g — absolute protein error
groundtruth_content — reference food items (comma-separated)
predicted_content — model-predicted food items
status — ok / failed

summary.json (aggregate)
rows_total — total number of rows
rows_ok — successfully processed rows
rows_failed — failed rows
mean_error_calories_signed — average signed calorie error
mean_error_calories_abs — average absolute calorie error
mean_error_protein_signed_g — average signed protein error
mean_error_protein_abs_g — average absolute protein error
cumulative_error_calories_signed — total signed calorie error
cumulative_error_protein_signed_g — total signed protein error
total_groundtruth_calories — sum of reference calories
total_predicted_calories — sum of predicted calories
total_groundtruth_protein_g — sum of reference protein
total_predicted_protein_g — sum of predicted protein
