# Benchmarks

This directory contains scripts for evaluating the calorie estimation pipeline on a labeled dataset.

## Dataset

The benchmark uses the **NutritionVerse-Real** dataset.

**Article** — https://arxiv.org/html/2401.08598v1
**Dataset** — https://www.kaggle.com/datasets/nutritionverse/nutritionverse-real?resource=download

Each image has ground truth nutritional values derived from measured ingredient weights.

Dataset location:

datasets/nutritionverse/
    images/
    metadata.csv

## Evaluation pipeline

food image
    ↓
meal canonicalization
    ↓
nutrition estimation
    ↓
prediction

## Metrics

The benchmark measures:

- Calories MAE  
- Protein MAE  
- Total Weight MAE

Where **MAE (Mean Absolute Error)** is the average absolute difference between predicted and true values.

## Running the benchmark

From the project root:

python benchmarks/run_nutritionverse.py