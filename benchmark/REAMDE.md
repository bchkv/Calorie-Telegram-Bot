Benchmark

This directory contains scripts and outputs for evaluating the app against a curated image benchmark dataset.

The benchmark is meant to test the image pipeline directly, not the Telegram bot layer.

Goal

For each benchmark image:
	1.	Run canonicalize_from_image(image_path, caption=None)
	2.	Convert the result into a canonical meal object
	3.	Run estimate_nutrition_from_canonical(meal)
	4.	Compare the predicted nutrition values against the ground-truth labels from the benchmark dataset
	5.	Save per-image results and aggregate metrics

This gives a simple end-to-end evaluation of the current image workflow.

⸻

What is being benchmarked

The current benchmark focuses on the image path only:

image -> canonical meal object -> nutrition estimate

This isolates the core meal understanding and estimation pipeline from unrelated layers such as:
	•	Telegram message handling
	•	database writes
	•	reply formatting
	•	UI concerns

⸻

Dataset location

The benchmark dataset is stored in a separate repository: the benchmark dataset builder.

That repository contains:
	•	curated benchmark images in data/processed/frames_selected/
	•	ground-truth labels in data/labels/labels.csv

The app repo should reference that dataset by path rather than duplicating the files here.

Expected structure in the dataset repo:

data/
    processed/
        frames_selected/
            1550706177_B.png
            1550710207_C.png
            ...

    labels/
        labels.csv

The labels.csv file is expected to contain rows like:

dish_id,camera,image_path,calories,mass_g,fat_g,carb_g,protein_g
1550706177,B,data/processed/frames_selected/1550706177_B.png,29.58,87.0,0.609,5.916,0.609

Important: image_path values are relative to the dataset repo root, not to this app repo.

⸻

Recommended usage

The benchmark runner should accept a dataset path argument, for example:

python benchmark/run_image_benchmark.py \
  --dataset-dir /path/to/nutrition5k_benchmark_dataset_builder

From that dataset directory, the script should resolve:
	•	labels file: data/labels/labels.csv
	•	image files: dataset_dir / row["image_path"]

This makes the benchmark reusable and avoids hardcoded absolute paths in code.

⸻

Expected benchmark flow

A typical benchmark run should:
	1.	Load labels.csv
	2.	Iterate over all benchmark rows
	3.	Resolve each image path from the dataset repo
	4.	Run image canonicalization
	5.	Run nutrition estimation
	6.	Save per-sample outputs into a results CSV
	7.	Print summary metrics

⸻

Suggested files in this directory

benchmark/
    README.md
    run_image_benchmark.py
    outputs/

Suggested output artifacts:
	•	outputs/image_benchmark_results.csv
	•	optional analysis files later, such as summary reports or plots

⸻

Suggested result fields

The benchmark results CSV should ideally include:

dish_id
camera
image_path
true_calories
pred_calories
calorie_error
abs_calorie_error
true_protein
pred_protein
protein_error
abs_protein_error
true_mass_g
pred_mass_g
mass_error_g
abs_mass_error_g
canonical_summary
predicted_dish
status
error_message

This is enough to:
	•	compute aggregate metrics
	•	inspect individual failures
	•	distinguish pipeline crashes from bad predictions
	•	understand whether errors come from canonicalization or estimation

⸻

Initial metrics

For the current app version, the most useful initial metrics are:
	•	Calories MAE
	•	Protein MAE
	•	Mass MAE
	•	optional median absolute error
	•	optional list of worst predictions

This is sufficient for a first internal benchmark.

⸻

Why this benchmark exists

The current app uses a multi-step meal pipeline:
	•	image -> canonical meal object
	•	canonical meal object -> nutrition estimate

Because of that, a benchmark should preserve the intermediate stage and make it inspectable.

If a prediction is poor, the benchmark output should help answer:
	•	was the meal recognized incorrectly from the image?
	•	or was the canonical meal recognized correctly, but estimated poorly?
	•	is the estimated portion size / mass far from the ground truth even when the dish type is roughly correct?
	•	is the estimated portion size / mass far from the ground truth even when the dish type is roughly correct?

That makes this benchmark useful not only for scoring but also for debugging.

⸻

Scope

This benchmark currently evaluates only the image input path.

It does not evaluate:
	•	text input benchmarking
	•	audio input
	•	Telegram bot interaction quality
	•	database persistence correctness
	•	UI formatting

Those can be benchmarked separately later.

⸻

Notes
	•	Keep this directory focused on benchmark code and outputs.
	•	Keep the curated dataset in the separate dataset repo.
	•	Prefer direct Python function calls over bot-level integration for benchmark runs.
	•	Treat this benchmark as a reproducible internal evaluation set for rapid iteration.