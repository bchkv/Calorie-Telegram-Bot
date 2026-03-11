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