# Calorie Telegram Bot TODO

## Pipeline Refactor

- [ ] Split meal processing into two stages
- [ ] Image -> meal description
- [ ] Meal description -> calorie & protein estimation
- [ ] Route text meals directly to the nutrition estimator
- [ ] Create separate modules (`vision.py` -> description, `nutrition.py` -> estimation)

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

## UX Improvements

- [ ] Shorten the line divider
- [ ] Add buttons: delete meal, show day log, set target
- [ ] Set daily goals interactively
- [ ] Add `/help` command
- [ ] Highlight large meals
- [ ] Improve description and start messages
