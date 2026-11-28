---
description: Run an ad-hoc gauntlet challenge session (5 questions, random scope)
---

# Gauntlet Challenge Session

Invoke `Skill(gauntlet:challenge)` once per question. Its generate,
present, evaluate and record steps cover one challenge, so a session
repeats them.

Arguments:

- No args: random scope, 5 questions
- `--count N`: repeat the skill's steps N times instead of 5
- `--scope <file>...`: pass the files to `challenge_engine.py --files`.
  It matches knowledge entries by file, so name files, not directories
- `--type <type>`: pass to `challenge_engine.py --type`
- `--source`, `--category`, `--difficulty`: pass through to
  `challenge_engine.py` unchanged (see the skill's step 3)
