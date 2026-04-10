---
name: justify
description: >-
  Audit changes for additive bias, Iron Law compliance,
  and minimal intervention. Justifies every change against
  a "simplest safe change" standard.
usage: /justify [--scope staged|branch|file] [path...]
---

# Justify Changes

Post-implementation audit that forces honest accounting
of every change. Detects AI additive bias, test-logic
tampering, and unnecessary complexity.

## Usage

```bash
# Justify all changes on the current branch
/justify

# Justify only staged changes
/justify --scope staged

# Justify specific files
/justify src/auth.py tests/test_auth.py
```

## What It Does

1. Loads the justify methodology:
   `Skill(imbue:justify)`
2. Gathers the change delta (git diff from base branch)
3. Computes an additive bias score
4. Checks Iron Law compliance (test logic tampering)
5. Runs minimal intervention analysis per file
6. Generates a justification report with risk assessment

## When to Use

- After completing implementation, before committing
- Before creating a PR
- When scope-guard flags RED or YELLOW zone
- After any session where significant code was added

## Arguments

| Argument | Description |
|----------|-------------|
| `--scope staged` | Only audit staged changes |
| `--scope branch` | Audit all branch changes (default) |
| `--scope file` | Audit specific files listed after |
| `path...` | Specific file paths to audit |
