---
schema: nightshift/handoff@1
item: NS-000
title: One line naming the outcome
base_branch: main
branch: night/NS-000-slug
scope:
  allow_paths:
    - path/to/source.py
    - path/to/test_file.py
  max_diff_lines: 200
  spec_ref: null
commands:
  setup: uv sync
  test: uv run pytest -q
  lint: uv run ruff check scripts/
  full_test: uv run pytest -q
budget:
  max_tasks: 6
  max_attempts_per_task: 3
  implementer_timeout_s: 900
  claude_token_ceiling: 120000
implementer:
  provider: auto
  allow_on_plan_fallback: false
babysitter:
  model: sonnet
---

## Definition of done

The single sentence the morning review checks.

## Out of scope

- Name the neighbouring change the night shift must not make.

## Known traps

Anything a cold session would get wrong. Directory-sensitive commands,
non-obvious fixture setup, functions that return a reason rather than
raising.
