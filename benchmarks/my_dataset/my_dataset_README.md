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
