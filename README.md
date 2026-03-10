## Current Workflow

The bot now uses a multi-step meal pipeline instead of estimating everything in a single step.

### High-level flow

There are two main input paths right now:

- **Text input** -> canonical meal parsing -> nutrition estimation
- **Image input** -> visual meal description -> nutrition estimation

Both paths converge into the same shared intermediate format: a **canonical meal object**.

---

## Files and responsibilities

### `bot.py`

This is the Telegram bot entrypoint and orchestration layer.

It:
- receives messages from users
- routes photo messages through the image pipeline
- routes text messages through the text pipeline
- saves final meal estimates to the database
- formats and sends replies back to the user

The bot should stay thin: it coordinates the pipeline but does not contain meal interpretation or nutrition logic itself.

---

### `vision.py`

Responsible for **image understanding**.

Main function:
- `describe_meal_from_image(image_path, caption=None)`

It takes:
- a saved image file path
- an optional user caption

It returns a **canonical meal object** describing what is visible in the image.

Example output:

```json
{
  "summary": "2 tuna salad toasts",
  "items": [
    {
      "name": "tuna salad toast",
      "quantity": 2,
      "unit": "pieces"
    }
  ],
  "notes": "open-faced, toasted bread"
}
```

Important: `vision.py` does **not** estimate calories or protein.

---

### `meal_parser.py`

Responsible for **text meal parsing**.

Main function:
- `parse_meal_from_text(text)`

It takes raw user text such as:

```text
2 tuna sandwiches and a banana
```

and converts it into the same canonical meal object format used by the image pipeline.

This keeps text and image inputs consistent internally.

Important: `meal_parser.py` does **not** estimate calories or protein.

---

### `nutrition_estimation.py`

Responsible for **nutrition estimation**.

Main function:
- `estimate_nutrition_from_canonical(meal)`

It takes a canonical meal object and returns the final nutrition estimate, currently:

- `dish`
- `calories`
- `protein`

Example output:

```json
{
  "dish": "2 tuna salad toasts",
  "calories": 420,
  "protein": 28
}
```

This module is shared by both the text and image pipelines.

---

### `db.py`

Responsible for data persistence.

It stores and retrieves:
- logged meals
- today's totals
- daily goals

The bot writes only the final estimated result into the database for now.

---

### `ui.py`

Responsible for formatting bot replies.

It formats:
- single meal responses
- today's totals
- today's meal list
- goal display and goal updates

This keeps presentation logic separate from bot handlers and pipeline logic.

---

## Pipeline details

### Text input flow

1. User sends a text message describing a meal
2. `bot.py` calls `parse_meal_from_text()` from `meal_parser.py`
3. The result is a canonical meal object
4. `bot.py` sends that object to `estimate_nutrition_from_canonical()` in `nutrition_estimation.py`
5. Final nutrition values are saved via `db.py`
6. Reply text is formatted via `ui.py`

---

### Image input flow

1. User sends a meal photo
2. `bot.py` downloads the image into `temp/`
3. `bot.py` calls `describe_meal_from_image()` from `vision.py`
4. The result is a canonical meal object
5. `bot.py` sends that object to `estimate_nutrition_from_canonical()` in `nutrition_estimation.py`
6. Final nutrition values are saved via `db.py`
7. Reply text is formatted via `ui.py`
8. Temporary image file is deleted

---

## Why this architecture is better

Previously, the bot tried to do everything in one step:
- detect the meal
- count items
- infer ingredients
- estimate calories and protein

That made the output more brittle and harder to debug.

The current architecture is better because it separates:

1. **input understanding**
2. **canonical meal representation**
3. **nutrition estimation**

Benefits:
- easier debugging
- more consistent handling of text and images
- easier future support for audio input
- better separation of responsibilities across files

---

## Planned extension: audio

The next logical step is:

- **Audio input** -> speech-to-text -> canonical meal parsing -> nutrition estimation

This will fit naturally into the same architecture because all modalities will converge into the same canonical meal object before estimation.
