# Calorie Telegram Bot -- MVP TODO

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