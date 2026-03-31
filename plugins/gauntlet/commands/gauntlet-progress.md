---
description: Show challenge accuracy stats, weak areas, and streak
model_hint: fast
---

# Gauntlet Progress

Show developer challenge statistics.

## Steps

1. Get developer ID from `git config user.email`
2. Load progress from `.gauntlet/progress/<developer>.json`
3. Display: overall accuracy, current streak, accuracy by category,
   total challenges, last session date
