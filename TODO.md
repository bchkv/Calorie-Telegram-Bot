# Calorie Telegram Bot -- MVP TODO

## Full async implementation

- [X] Use AsyncOpenAI

## Proper logging implementation

- [X] Use Logging

## Stability & Reliability
- [ ] Restart the bot automatically if it crashes (systemd on Linux)
- [ ] Add global error handler for aiogram
- [ ] Wrap OpenAI calls in try/except
- [ ] Wrap DB operations in try/except
- [ ] Log errors to console

## File Handling
- [ ] Delete temp image after processing
- [ ] Ensure temp folder exists at startup
- [ ] Ignore non-image files accidentally sent

## Meal Handling
- [ ] Enumerate meals for the current day
- [ ] Show numbered list of meals for today
- [ ] Add command to view today's meals (/today)

## Meal Editing
- [ ] Add functionality to delete meals from the list
- [ ] Add command /delete <number>
- [ ] Confirm deletion before removing meal

## Nutrition Goals
- [ ] Add daily calorie goal
- [ ] Add daily protein goal
- [ ] Show progress toward goals

## Day Handling
- [ ] Add setting to define the start of a new day
- [ ] Allow user to set their timezone
- [ ] Reset daily totals based on chosen day start

## UX Improvements
- [ ] Ignore commands in text meal handler
- [ ] Handle empty messages
- [ ] Add /help command

## Final MVP Features
- [ ] Photo meal estimation
- [ ] Text meal estimation
- [ ] Store meals in SQLite
- [ ] Show daily totals
- [ ] Track calories and protein
- [ ] Basic error handling
