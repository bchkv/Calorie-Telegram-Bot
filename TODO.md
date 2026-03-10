# Calorie Telegram Bot TODO

## Core Refactor

- [ ] Split meal processing into 3 stages:
  - [ ] input understanding
  - [ ] canonical meal parsing
  - [ ] nutrition estimation
- [ ] Unify all modalities around one shared canonical meal object
- [ ] Keep the Telegram bot layer thin and route all logic through services

## Pipeline Design

- [ ] Text -> canonical meal object -> nutrition estimation
- [ ] Image -> visual meal description -> canonical meal object -> nutrition estimation
- [ ] Audio -> speech-to-text -> canonical meal object -> nutrition estimation
- [ ] Decide canonical meal object schema
- [ ] Store both `summary` and structured `items`
- [ ] Decide how to represent uncertainty / assumptions internally

## Project Structure

- [ ] Move code into `app/`
- [ ] Add `app/config.py`
- [ ] Add `app/bot/handlers.py`
- [ ] Add `app/storage/db.py`
- [ ] Add `app/services/vision.py`
- [ ] Add `app/services/meal_parser.py`
- [ ] Add `app/services/nutrition.py`
- [ ] Add `app/services/audio.py`
- [ ] Add `app/ui/formatting.py`
- [ ] Add `app/prompts/`
- [ ] Add `main.py` as the entrypoint
- [ ] Create `data/` for persistent files
- [ ] Create `temp/` for temporary runtime files
- [ ] Add `tests/`

## Canonical Meal Object

- [ ] Define canonical schema, e.g.:
  - [ ] `summary`
  - [ ] `items[]`
  - [ ] `quantity`
  - [ ] `unit`
  - [ ] optional `notes`
- [ ] Decide whether image parsing should output canonical form directly
- [ ] Decide how vague text inputs should map into canonical form
- [ ] Add examples of canonical objects for common meals

## Bot Layer

- [ ] Keep `bot.py` minimal or replace with `main.py`
- [ ] Move handlers out of the root into `app/bot/handlers.py`
- [ ] Add `/help` handler
- [ ] Add `/delete_all_today` or similar command
- [ ] Add support for editing or replacing logged meals
- [ ] Add buttons for common actions:
  - [ ] delete meal
  - [ ] show day log
  - [ ] set goal

## Features

- [ ] Audio message support
- [ ] Stats support
- [ ] Average stats tracker
- [ ] More nutrients support with settings
- [ ] Data export functionality
- [ ] Trend tracker
- [ ] Trend extrapolation
- [ ] User-editable estimated meals after logging

## Shortcut / API Support

- [ ] Add `app/api/server.py`
- [ ] Reuse the same core meal pipeline from the API
- [ ] Run an HTTPS server
- [ ] Make the Shortcut
- [ ] Send meal data from Shortcut to the server
- [ ] Share/log the result in the bot
- [ ] Add auth token for Shortcut -> server requests
- [ ] Validate incoming request schema
- [ ] Add basic rate limiting / abuse protection
- [ ] Decide where the server will be hosted
- [ ] Add HTTPS deployment plan

## Reliability / Quality

- [ ] Add golden test cases for meal parsing and estimation
- [ ] Save sample text/photo inputs for regression testing
- [ ] Compare old vs new pipeline on the same examples
- [ ] Add sanity checks for obviously wrong totals
- [ ] Add fallback behavior when description extraction is uncertain
- [ ] Add fallback behavior when estimation is uncertain
- [ ] Add regression cases for repeated identical items
- [ ] Test vague vs detailed user inputs

## Data / DB

- [ ] Decide DB location under `data/`
- [ ] Add DB initialization
- [ ] Add simple migrations strategy
- [ ] Store original input source (`text`, `image`, later `audio`)
- [ ] Store original raw user input where useful
- [ ] Store intermediate visual/text description for debugging
- [ ] Store canonical meal object for debugging
- [ ] Add backup/export plan

## Observability

- [ ] Improve structured logging
- [ ] Log pipeline stage failures separately
- [ ] Add debug mode for inspecting:
  - [ ] raw input
  - [ ] extracted description
  - [ ] canonical meal object
  - [ ] final estimate
- [ ] Add request IDs / meal IDs in logs

## Prompt / Model Work

- [ ] Version prompts
- [ ] Move prompt templates into dedicated modules/files
- [ ] Test `detail: low` vs `high`
- [ ] Evaluate whether bigger models are worth the cost
- [ ] Define fallback model strategy
- [ ] Add targeted prompts for:
  - [ ] visual description extraction
  - [ ] text-to-canonical parsing
  - [ ] nutrition estimation
- [ ] Add test cases for quantity consistency

## Product Decisions

- [ ] Decide when to ask follow-up questions
- [ ] Decide how vague inputs should be handled
- [ ] Decide whether to show assumptions to the user
- [ ] Decide whether users can edit estimated meals after logging
- [ ] Decide whether to show intermediate meal interpretation on demand

## UX Improvements

- [ ] Shorten the line divider
- [ ] Improve start/help messages
- [ ] Highlight large meals
- [ ] Set daily goals interactively
- [ ] Improve deletion UX
- [ ] Make replies more compact but still readable

## Nice-to-Have

- [ ] Support barcode/product input later
- [ ] Support recipe-style multi-ingredient input
- [ ] Support meal confirmation flow for uncertain cases