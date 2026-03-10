# Calorie Telegram Bot TODO

## Pipeline Refactor

- [ ] Split meal processing into two stages
- [ ] Image -> meal description
- [ ] Meal description -> calorie & protein estimation
- [ ] Route text meals directly to the nutrition estimator
- [ ] Create separate modules (`vision.py` -> description, `nutrition.py` -> estimation)
- [x] Show progress toward goals

## Project Structure

- [ ] Move code into `app/`
- [ ] Add `app/storage/db.py`
- [ ] Add `app/bot/handlers.py`
- [ ] Add `app/api/server.py`
- [ ] Add `app/config.py`
- [ ] Add `main.py` as the entrypoint
- [ ] Create `data/` for persistent files
- [ ] Create `temp/` for temporary runtime files
- [ ] Add `tests/`

## Features

- [ ] Delete all today records option
- [ ] Enable editing messages
- [ ] Audio message support
- [ ] Stats support
- [ ] Average stats tracker
- [ ] More nutrients support with settings
- [ ] Data export functionality
- [ ] Trend tracker and data extrapolation

## Shortcut Support

- [ ] Run an HTTPS server
- [ ] Make the Shortcut
- [ ] Send meal data from Shortcut to your server
- [ ] Reuse the same core meal pipeline from the server
- [ ] Share/log the result in the bot
- [ ] Add auth token for Shortcut -> server requests
- [ ] Validate incoming request schema
- [ ] Add rate limiting / basic abuse protection
- [ ] Decide where the server will be hosted
- [ ] Add HTTPS deployment plan

## Reliability / Quality

- [ ] Add golden test cases for meal estimation
- [ ] Save sample text/photo inputs for regression testing
- [ ] Compare old vs new pipeline on the same examples
- [ ] Add sanity checks for obviously wrong totals
- [ ] Add fallback behavior when description extraction is uncertain

## Data / DB

- [ ] Decide DB location (`data/`)
- [ ] Add DB initialization / migrations
- [ ] Store original input source (`text`, `image`, later `audio`)
- [ ] Store intermediate meal description for debugging
- [ ] Add backup/export plan

## Observability

- [ ] Improve structured logging
- [ ] Log pipeline stage failures separately
- [ ] Add debug mode for inspecting description vs estimation
- [ ] Add request IDs / meal IDs in logs

## Prompt / Model Work

- [ ] Version prompts
- [ ] Keep prompt templates in dedicated files/modules
- [ ] Test `detail: low` vs `high`
- [ ] Evaluate whether bigger models are worth the cost
- [ ] Define fallback model strategy

## Product Decisions

- [ ] Decide when to ask follow-up questions
- [ ] Decide how vague inputs should be handled
- [ ] Decide whether to show assumptions to the user
- [ ] Decide whether users can edit estimated meals after logging

## UX Improvements

- [ ] Shorten the line divider
- [ ] Add buttons: delete meal, show day log, set target
- [ ] Set daily goals interactively
- [ ] Add `/help` command
- [ ] Highlight large meals
- [ ] Improve description and start messages
