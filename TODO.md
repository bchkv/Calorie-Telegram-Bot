# Calorie Telegram Bot -- MVP TODO

## Architecture Improvement
- [ ] Split meal processing into two stages
- [ ] Image → meal description
- [ ] Meal description → calorie & protein estimation
- [ ] Route text meals directly to the nutrition estimator
- [ ] Create separate modules (vision.py → description, nutrition.py → estimation)
- [ ] Log intermediate description for debugging

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
- [ ] If the meal is large, you can highlight it

## Final MVP Features
- [ ] Photo meal estimation
- [ ] Text meal estimation
- [ ] Store meals in SQLite
- [ ] Show daily totals
- [ ] Track calories and protein
- [ ] Basic error handling