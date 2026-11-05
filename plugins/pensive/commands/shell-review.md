---
name: shell-review
description: Audit shell scripts for correctness, safety, and portability.
---

# Shell Script Review Command

Audit shell scripts for correctness, safety, and portability.

## Usage

```bash
/shell-review [path/to/script.sh]
```

Without arguments, reviews all `.sh` files in `scripts/` and `.git/hooks/`.

## What It Does

Invoke `Skill(pensive:unified-review)` in its shell focus, the same as
`/full-review shell`. Its `modules/shell-review.md` carries the audit
workflow, the anti-pattern checks and the output format.
