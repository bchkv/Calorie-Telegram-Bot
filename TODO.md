# Calorie Telegram Bot -- MVP TODO

- store long-term stat
- add delete button after each added meal
- meal added date should match when user sent the message (so if the bot has been offline it doesn't disrupt the log)
- add export all data functionality so user can analyze it himself

## Architecture Improvement
- [ ] Split meal processing into two stages
- [ ] Image → meal description
- [ ] Meal description → calorie & protein estimation
- [ ] Route text meals directly to the nutrition estimator
- [ ] Create separate modules (vision.py → description, nutrition.py → estimation)
- [X] Show progress toward goals

## UX Improvements
- [ ] Set daily goals interactively
- [ ] Add /help command
- [ ] If the meal is large, you can highlight it

## Final MVP Features
- [ ] Photo meal estimation
- [ ] Text meal estimation
- [ ] Store meals in SQLite
- [ ] Show daily totals
- [X] Track calories and protein
- [X] Basic error handling

# Dev branch todo export

# Calorie Telegram Bot TODO

## Pipeline Design

- [ ] Add `tests/`

## Future Features

- [ ] Audio message support
- [ ] Stats support
- [ ] Average stats tracker
- [ ] More nutrients support with settings
- [ ] Data export functionality
- [ ] Trend tracker
- [ ] Trend extrapolation
- [ ] User-editable estimated meals after logging
- - [ ] Add `/help` handler
- [ ] Add `/delete_all_today` or similar command
- [ ] Add support for editing or replacing logged meals

allow user to export raw data in .csv

Buttons:

- [ ] delete meal
- [ ] show day log
- [ ] set goal
- [ ] Add `app/api/server.py`
- [ ] Reuse the same core meal pipeline from the API
- [ ] Run an HTTPS server
- [ ] Make the Shortcut
- [ ] Send meal data from Shortcut to the server
- [ ] Share/log the result in the bot

Security:

- [ ] Add auth token for Shortcut -> server requests
- [ ] Validate incoming request schema
- [ ] Add basic rate limiting / abuse protection
- 
- [ ] Improve structured logging
