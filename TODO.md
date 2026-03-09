# Calorie Telegram Bot -- MVP TODO

## Architecture Improvement
- [ ] Split meal processing into two stages
- [ ] Image → meal description
- [ ] Meal description → calorie & protein estimation
- [ ] Route text meals directly to the nutrition estimator
- [ ] Create separate modules (vision.py → description, nutrition.py → estimation)
- [ ] Log intermediate description for debugging

- [ ] Show progress toward goals

## Day Handling
- [ ] Add setting to define the start of a new day
- [ ] Allow user to set their timezone
- [ ] Reset daily totals based on chosen day start

## UX Improvements
- [ ] Set daily goals interactively
- [ ] Ignore commands in text meal handler
- [ ] Handle empty messages
- [ ] Add /help command
- [ ] If the meal is large, you can highlight it

## Final MVP Features
- [ ] Photo meal estimation
- [ ] Text meal estimation
- [ ] Store meals in SQLite
- [ ] Show daily totals
- [ ] Track calories and protein
- [ ] Basic error handling