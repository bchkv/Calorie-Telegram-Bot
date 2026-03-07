# Calorie Telegram Bot -- MVP TODO

Build the project step-by-step so that the bot is runnable after every
stage.

------------------------------------------------------------------------

## Stage 1 --- Make the bot alive

Goal: confirm Telegram integration works.

-   [x] Load environment variables from `.env`
-   [x] Initialize `Bot` and `Dispatcher`
-   [x] Implement `/start` command
-   [x] Respond to any text message with a simple reply (e.g., "ok")
-   [x] Run the bot locally and verify responses

Result: the bot responds to `/start` and text messages.

------------------------------------------------------------------------

## Stage 2 --- Receive photos

Goal: verify that the bot receives the exact input your app needs.

-   [x] Add handler for messages containing photos
-   [x] Detect `message.photo`
-   [x] Reply with "got photo"
-   [x] If caption exists, include it in the reply
-   [x] Log the caption to console

Result: bot correctly recognizes photo messages.

------------------------------------------------------------------------

## Stage 3 --- Download photo locally

Goal: obtain real image files inside the application.

-   [x] Extract highest resolution photo (`message.photo[-1]`)
-   [x] Request file info from Telegram API
-   [x] Download file locally
-   [x] Save to `temp/` folder
-   [x] Print saved path to console
-   [x] Reply "photo saved"

Result: photo is downloaded and saved locally.

------------------------------------------------------------------------

## Stage 4 --- Stub AI layer

Goal: connect bot logic with estimation logic.

In `vision.py`:

-   [x] Implement `estimate_meal(image_path, description)`
-   [x] Return fake data for now:

Example structure:

    {
        "dish": "test meal",
        "calories": 500,
        "protein": 30
    }

In `bot.py`:

-   [x] Call `estimate_meal()`
-   [x] Format reply with calories and protein
-   [x] Send reply to user

Result: full pipeline exists even with fake AI.

------------------------------------------------------------------------

## Stage 5 --- Add SQLite storage

Goal: persist meals and compute totals.

In `db.py`:

-   [x] Initialize SQLite database
-   [x] Create `meals` table if not exists

Table fields:

    id
    user_id
    dish
    calories
    protein
    created_at

Functions:

-   [x] `add_meal(user_id, dish, calories, protein)`
-   [x] `get_today_totals(user_id)`

In `bot.py`:

-   [x] Save estimated meal
-   [x] Retrieve today's totals
-   [x] Include totals in reply

Result: meals persist and daily totals work.

------------------------------------------------------------------------

## Stage 6 --- Add /today command

Goal: allow user to check totals without sending photos.

-   [ ] Implement `/today`
-   [ ] Query totals from database
-   [ ] Return calories and protein totals

Result: basic tracking functionality exists.

------------------------------------------------------------------------

## Stage 7 --- Replace fake estimator with real model

Goal: implement real AI-based estimation.

In `vision.py`:

-   [ ] Send image + description to vision model

-   [ ] Ask for structured JSON output

-   [ ] Parse response

-   [ ] Return dict:

    { "dish": "...", "calories": ..., "protein": ... }

Result: real calorie estimation.

------------------------------------------------------------------------

## Stage 8 --- Basic robustness

Goal: prevent obvious failures.

-   [ ] Handle missing caption
-   [ ] Handle model errors
-   [ ] Handle DB errors
-   [ ] Delete temp image after processing
-   [ ] Log errors to console

Result: MVP becomes stable enough to run continuously.

------------------------------------------------------------------------

## Final MVP Features

-   [ ] Photo-based meal estimation
-   [ ] Optional text description
-   [ ] Calorie estimation
-   [ ] Protein estimation
-   [ ] Daily tracking
-   [ ] `/today` command
